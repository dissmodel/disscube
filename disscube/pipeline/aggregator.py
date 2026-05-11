from disscube.pipeline import PipelineStage, PipelineContext
from disscube.operators import ZonalAggregator, ProximityAggregator
import xarray as xr
import numpy as np

class Aggregator(PipelineStage):
    def execute(self, ctx: PipelineContext) -> PipelineContext:
        grid = ctx.grid
        vars = ctx.derivation.variables
        data = ctx.data
        
        results = {}
        for i, var in enumerate(vars):
            # Selection logic for multi-band DataArray
            var_data = data
            if isinstance(data, xr.DataArray) and "band" in data.dims and data.sizes["band"] > 1:
                # Use band_map if available, otherwise fallback to positional index
                if ctx.source.band_map and var.name in ctx.source.band_map:
                    band_idx = ctx.source.band_map[var.name] - 1 # 1-based to 0-based
                    if 0 <= band_idx < data.sizes["band"]:
                        var_data = data.isel(band=band_idx)
                    else:
                        raise ValueError(f"Band index {band_idx+1} for variable '{var.name}' is out of range. Data has {data.sizes['band']} bands.")
                elif i < data.sizes["band"]:
                    var_data = data.isel(band=i)
                else:
                    raise ValueError(f"No band available for variable '{var.name}' at index {i}. Data has {data.sizes['band']} bands and no band_map was provided.")

            if var.operator in ["mean", "sum", "std", "min", "max", "majority", "minority", "percentage", "attribute", "presence"]:
                res = ZonalAggregator.aggregate(var_data, [var], grid)
            elif var.operator in ["min_distance", "count"]:
                res = ProximityAggregator.aggregate(var_data, [var], grid)
            else:
                raise ValueError(f"Unknown operator: {var.operator}")
            
            # Drop 'band' dimension if it exists to allow merging into Dataset
            if "band" in res.coords:
                res = res.drop_vars("band")
            results[var.name] = res
        
        # Merge all results into a single xarray Dataset
        ds = xr.Dataset(results)
        ctx.data = ds
        return ctx
