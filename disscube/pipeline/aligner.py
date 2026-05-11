import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
import xarray as xr
import numpy as np
from disscube.pipeline import PipelineStage, PipelineContext
from disscube.models import GridSpec

class GridAligner(PipelineStage):
    def execute(self, ctx: PipelineContext) -> PipelineContext:
        grid = ctx.grid
        fmt = ctx.source.format
        
        if fmt == "raster":
            # For raster, we'll use rasterio to reproject/crop to grid bbox/resolution
            ctx.data = self._align_raster(ctx.source.asset_url, grid)
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

    def _align_raster(self, url: str, grid: GridSpec) -> xr.DataArray:
        import rioxarray
        from shapely.geometry import box
        
        # Load the raster
        ds = rioxarray.open_rasterio(url)
        
        # Ensure it's EPSG:31983 or whatever the grid expects
        if ds.rio.crs != grid.crs:
            ds = ds.rio.reproject(grid.crs)
            
        # Select resolution and extent
        # We use reproject to resample to the exact grid resolution and alignment
        # This is more robust than just clipping
        from rasterio.warp import Resampling
        
        # Create target coords
        import numpy as np
        rows = int((grid.bbox[3] - grid.bbox[1]) / grid.resolution)
        cols = int((grid.bbox[2] - grid.bbox[0]) / grid.resolution)
        
        # Target transform
        from affine import Affine
        target_transform = Affine.translation(grid.bbox[0], grid.bbox[3]) * Affine.scale(grid.resolution, -grid.resolution)
        
        # Use rioxarray's reproject to match the target grid perfectly
        aligned = ds.rio.reproject(
            grid.crs,
            shape=(rows, cols),
            transform=target_transform,
            resampling=Resampling.nearest
        )
        
        return aligned
