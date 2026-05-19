from disscube.pipeline import PipelineStage, PipelineContext
from disscube.operators import ZonalAggregator, ProximityAggregator
import xarray as xr
import numpy as np


def _crs_to_named_wkt(crs_str: str) -> str:
    """
    Converts a CRS string (proj4, EPSG, or WKT) to a WKT string with a
    human-readable name. This prevents rioxarray from writing PROJCS["unknown"]
    when the CRS has no official EPSG code (e.g. BDC Albers).
    """
    from pyproj import CRS

    crs = CRS.from_user_input(crs_str)

    # If pyproj already resolved a name, use it as-is
    if crs.name and crs.name.lower() != "unknown":
        return crs.to_wkt()

    # BDC Albers: assign a stable name so QGIS and other tools can identify it
    bdc_albers_proj4 = (
        "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 "
        "+x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
    )
    bdc_ref = CRS.from_proj4(bdc_albers_proj4)
    if crs.equals(bdc_ref):
        # Re-create from ESRI WKT with explicit name — QGIS recognises this
        named_wkt = (
            'PROJCS["Brazil_Albers_Equal_Area_Conic",'
            'GEOGCS["GCS_SIRGAS_2000",'
            'DATUM["SIRGAS_2000",'
            'SPHEROID["GRS_1980",6378137,298.257222101]],'
            'PRIMEM["Greenwich",0],'
            'UNIT["Degree",0.017453292519943295]],'
            'PROJECTION["Albers_Conic_Equal_Area"],'
            'PARAMETER["False_Easting",5000000],'
            'PARAMETER["False_Northing",10000000],'
            'PARAMETER["longitude_of_center",-54],'
            'PARAMETER["Standard_Parallel_1",-2],'
            'PARAMETER["Standard_Parallel_2",-22],'
            'PARAMETER["latitude_of_center",-12],'
            'UNIT["Meter",1]]'
        )
        return named_wkt

    # Fallback: return whatever pyproj generates
    return crs.to_wkt()


class Aggregator(PipelineStage):
    def execute(self, ctx: PipelineContext) -> PipelineContext:
        grid = ctx.grid
        vars = ctx.derivation.variables
        data = ctx.data

        # Initial empty dataset with correct grid coords
        final_ds = xr.Dataset(coords={"y": grid.ys, "x": grid.xs})

        # Write CRS using named WKT so tools like QGIS don't fall back to
        # EPSG:4326 when the CRS has no official EPSG code (e.g. BDC Albers).
        named_wkt = _crs_to_named_wkt(grid.crs)
        final_ds.rio.write_crs(named_wkt, inplace=True)
        final_ds.rio.write_transform(grid.transform, inplace=True)

        # Preserve spatial_ref before any merge — compat="override" can silently
        # replace it with the CRS from the aggregation result (e.g. EPSG:4674),
        # causing QGIS and other tools to misread the output CRS.
        spatial_ref = final_ds.coords.get("spatial_ref")

        for i, var in enumerate(vars):
            # Selection logic for multi-band DataArray
            var_data = data
            if isinstance(data, xr.DataArray) and "band" in data.dims and data.sizes["band"] > 1:
                # Use band_map if available, otherwise fallback to positional index
                if ctx.source.band_map and var.name in ctx.source.band_map:
                    band_idx = ctx.source.band_map[var.name] - 1  # 1-based to 0-based
                    if 0 <= band_idx < data.sizes["band"]:
                        var_data = data.isel(band=band_idx)
                    else:
                        raise ValueError(
                            f"Band index {band_idx+1} for variable '{var.name}' is out of range. "
                            f"Data has {data.sizes['band']} bands."
                        )
                elif i < data.sizes["band"]:
                    var_data = data.isel(band=i)
                else:
                    raise ValueError(
                        f"No band available for variable '{var.name}' at index {i}. "
                        f"Data has {data.sizes['band']} bands and no band_map was provided."
                    )

            if var.operator in ["mean", "sum", "std", "min", "max", "majority", "minority", "percentage", "attribute", "presence"]:
                res = ZonalAggregator.aggregate(var_data, [var], grid)
            elif var.operator in ["min_distance", "count"]:
                res = ProximityAggregator.aggregate(var_data, [var], grid)
            else:
                raise ValueError(f"Unknown operator: {var.operator}")

            # Merging result into final dataset
            if isinstance(res, xr.Dataset):
                if var.name in res.data_vars:
                    final_ds[var.name] = res[var.name]
                else:
                    final_ds = final_ds.merge(res, compat="override")
            else:
                final_ds[var.name] = res

            # Restore spatial_ref after every merge — compat="override" may have
            # replaced it with the result's CRS coordinate.
            if spatial_ref is not None:
                final_ds = final_ds.assign_coords({"spatial_ref": spatial_ref})

        ctx.data = final_ds
        return ctx
