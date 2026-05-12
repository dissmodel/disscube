from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable
import os

# Initialize client
cube = CubeClient(catalog="catalog.db", store="./data/")

grid_id = "BR/5km"
source_id = "slope_brazil"

# 1. Define Derivation
# We want the average slope in each 5km cell
derivation = SpatialDerivation(
    source_id=source_id,
    grid_id=grid_id,
    role="driver",
    variables=[
        Variable(name="major_slope", operator="majority")
    ]
)

print(f"Deriving {source_id} to {grid_id}...")
try:
    cube.derive(derivation)
    print("Derivation successful.")
    
    # Verify result
    derived = cube.search(grid=grid_id, role="driver")
    for d in derived:
        if "major_slope" in d.name:
            print(f"Result saved at: {d.asset_url}")
            
except Exception as e:
    print(f"Error: {e}")
