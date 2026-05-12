from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable
import os

# Initialize client
cube = CubeClient(catalog="catalog.db", store="./data/")

# 1. Check if the grid and source exist
grid_id = "BDC_100m"
source_id = "urban_centers" 
tile_id = "009002"

grid = cube.catalog.get_grid(grid_id)
source = cube.catalog.get_spatial_source(source_id)

if not grid:
    print(f"Error: Master Grid {grid_id} not found in catalog.")
    exit(1)

if not source:
    print(f"Error: Source {source_id} not found in catalog.")
    exit(1)

print(f"Target Master Grid: {grid_id}")
print(f"Target Tile: {tile_id}")
print(f"Source: {source_id} ({source.asset_url})")

# 2. Declare SpatialDerivation
derivation = SpatialDerivation(
    source_id=source_id,
    grid_id=grid_id,
    role="driver",
    variables=[
        Variable(name="dist_sedes", operator="min_distance")
    ]
)

# 3. Execute pipeline (derive) for the specific tile
print(f"\nExecuting distance derivation for tile {tile_id}...")
try:
    derived_vars = cube.derive(derivation, tile_id=tile_id)
    print("Derivation successful.")
    
    # 4. Load result to verify
    if derived_vars:
        var = derived_vars[0]
        res = cube.load(var.name, tile_id=tile_id)
        print(f"Result loaded successfully.")
        print(f" - Variable: {var.name}")
        print(f" - Tile: {tile_id}")
        print(f" - Shape: {res.shape}")
        print(f" - Path: {var.asset_url}")
    
except Exception as e:
    print(f"Error during derivation: {e}")
    import traceback
    traceback.print_exc()
