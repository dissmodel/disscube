from disscube.client import CubeClient
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable
import os

# Setup local paths
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/derived", exist_ok=True)

cube = CubeClient(catalog="catalog.db", store="./data/")

# 1. Register Grid
acre_grid = GridSpec(
    id="acre_5km",
    type="local",
    crs="EPSG:31983",
    resolution=5000.0,
    bbox=[300000, 8700000, 700000, 9100000],
    description="Acre 5km Grid"
)
cube.register_grid(acre_grid)

# 2. Register SpatialSource (Placeholder URI)
roads = SpatialSource(
    id="roads_v1",
    name="Main Roads",
    format="vector",
    asset_url="data/raw/roads.shp", # Assume this exists for the example
    crs="EPSG:31983"
)
cube.register_spatial_source(roads)

# 3. Derive Variable
derivation = SpatialDerivation(
    source_id="roads_v1",
    grid_id="acre_5km",
    role="driver",
    variables=[
        Variable(name="dist_roads", operator="min_distance")
    ]
)

print(f"Spec Hash: {derivation.spec_hash()}")

# In a real scenario, we'd call cube.derive(derivation)
# For this example, we'll just show the API
print("Derivation declared.")
