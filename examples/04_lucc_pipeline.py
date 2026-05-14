import os
from disscube.client import CubeClient
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable

cube = CubeClient(catalog="catalog.db", store="./data/")

# 1. Use BR/5km as reference grid (National, BDC Albers)
grid_id = "BR/5km"
# Tiles covering Acre
tiles = ['002006', '002007', '002008', '003007', '003008', '004007', '004008', '005007', '005008', '006008']

# 2. Register Source
proj_acre = "+proj=poly +lat_0=0 +lon_0=-54 +x_0=0 +y_0=0 +ellps=aust_SA +units=m +no_defs"

asset_path = "data/raw/acre_data.zip"
if not os.path.exists(asset_path):
    asset_path = "../disslucc-continuous/examples/data/input/csAC.zip"

data_source = SpatialSource(
    id="acre_base_bdc",
    name="Acre Vector Data (for BDC alignment)",
    format="vector",
    asset_url=asset_path,
    crs=proj_acre
)
cube.register_spatial_source(data_source)

# 3. Process each tile on the National Grid
variables_spec = [
    Variable(name="f", operator="attribute"),
    Variable(name="d", operator="attribute")
]

for tile_id in tiles:
    print(f"\n>>> Processing Tile {tile_id} for {grid_id} (National Alignment)...")
    derivation = SpatialDerivation(
        source_id="acre_base_bdc",
        grid_id=grid_id,
        role="luc_observation",
        variables=variables_spec
    )
    
    try:
        cube.derive(derivation, tile_id=tile_id)
        print(f"Success for Tile {tile_id}")
        
        # Optional: Load and check
        da_f = cube.load("f", tile_id=tile_id, grid_id=grid_id)
        print(f"Tile {tile_id} variable 'f' shape: {da_f.shape}, mean: {da_f.mean().values:.4f}")
    except Exception as e:
        print(f"Error for Tile {tile_id}: {e}")

print("\nAcre LUCC Tiled National Pipeline Finished.")
