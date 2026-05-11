import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
import xarray as xr
import numpy as np
from disscube.pipeline import PipelineStage, PipelineContext
from disscube.models import GridSpec, Variable

class GridAligner(PipelineStage):
    def execute(self, ctx: PipelineContext) -> PipelineContext:
        grid = ctx.grid
        fmt = ctx.source.format
        
        if fmt == "raster":
            # For raster, we'll use rasterio to reproject/crop to grid bbox/resolution
            # Pass variables to decide resampling method
            ctx.data = self._align_raster(ctx.source.asset_url, grid, ctx.derivation.variables)
        elif fmt == "vector":
            # For vector, ensure CRS matches grid
            gdf = ctx.data
            if gdf.crs != grid.crs:
                gdf = gdf.to_crs(grid.crs)
            # Crop to bbox
            from shapely.geometry import box
            bbox_geom = box(*grid.bbox)
            gdf = gdf.clip(bbox_geom)
            ctx.data = gdf
            
        return ctx

    def _align_raster(self, url: str, grid: GridSpec, variables: list[Variable] = None) -> xr.DataArray:
        import rioxarray
        from rasterio.warp import Resampling
        from affine import Affine
        
        # Load the raster
        ds = rioxarray.open_rasterio(url)
        
        # Determine resampling method based on operator
        resampling_method = Resampling.nearest
        if variables:
            op = variables[0].operator.lower()
            if op in ["mean", "average"]:
                resampling_method = Resampling.average
            elif op in ["majority", "mode"]:
                resampling_method = Resampling.mode
            elif op == "max":
                resampling_method = Resampling.max
            elif op == "min":
                resampling_method = Resampling.min
            elif op == "sum":
                resampling_method = Resampling.sum

        # Target size
        rows = grid.rows
        cols = grid.cols
        
        # Target transform
        target_transform = grid.transform
        
        # Use rioxarray's reproject to match the target grid perfectly
        aligned = ds.rio.reproject(
            grid.crs,
            shape=(rows, cols),
            transform=target_transform,
            resampling=resampling_method
        )
        
        return aligned
