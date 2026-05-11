from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable
import os

# Initialize client
cube = CubeClient(catalog="catalog.json", store="./data/")

# 1. Check if the grid and source exist
grid_id = "BDC_LG_009002"
source_id = "urban_centers"

grid = cube.catalog.get_grid(grid_id)
source = cube.catalog.get_spatial_source(source_id)

if not grid:
    print(f"Error: Grid {grid_id} not found in catalog.")
    exit(1)

if not source:
    print(f"Error: Source {source_id} not found in catalog.")
    exit(1)

print(f"Target Grid: {grid_id}")
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

# 3. Execute pipeline (derive)
print("\nExecuting distance derivation (ProximityAggregator)...")
try:
    cube.derive(derivation)
    print("Derivation successful.")
    
    # 4. Load result to verify
    derived = cube.search(grid=grid_id, role="driver")
    for d in derived:
        if "dist_sedes" in d.name:
            print(f"Result saved at: {d.asset_url}")
            
except Exception as e:
    print(f"Error during derivation: {e}")
    print("\nNote: Ensure the source file exists at the specified path.")
