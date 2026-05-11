import rasterio
import geopandas as gpd
from disscube.pipeline import PipelineStage, PipelineContext

class Normalizer(PipelineStage):
    def execute(self, ctx: PipelineContext) -> PipelineContext:
        url = ctx.source.asset_url
        fmt = ctx.source.format
        
        if fmt == "raster":
            with rasterio.open(url) as src:
                # Validation only, don't read yet or just check metadata
                pass
        elif fmt == "vector":
            # For vector, we often need to load it to validate
            gdf = gpd.read_file(url)
            ctx.data = gdf
        else:
            raise ValueError(f"Unknown format: {fmt}")
            
        return ctx
