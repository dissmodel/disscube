from disscube.client import CubeClient
from disscube.models import SpatialSource

cube = CubeClient(catalog="catalog.db", store="./data/")

# Acre tiles
tiles = ['002006', '002007', '002008', '003007', '003008', '004007', '004008', '005007', '005008', '006008']

# We need to register these tiles specifically for the BR/5km grid 
# so the derive(tile_id=...) method can find their bboxes.
for tile_id in tiles:
    # Get bbox from the MD version
    md_source = cube.catalog.get_spatial_source(f"BDC_MD_{tile_id}")
    if md_source:
        source = SpatialSource(
            id=f"BR/5km_{tile_id}",
            name=f"BR 5km Tile {tile_id}",
            format="raster",
            asset_url=f"data/derived/BR/5km/{tile_id}", # Placeholder
            crs=md_source.crs,
            bbox=md_source.bbox
        )
        cube.register_spatial_source(source)
        print(f"Registered tile {tile_id} for BR/5km")
