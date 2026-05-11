
from disscube.client import CubeClient
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable
import os

cube = CubeClient(catalog="catalog.json", store="./data/")

# 1. Register a Grid for All Brazil (5km resolution, EPSG:5880)
# Bounds based on the PNLT vector data extent we just verified
grid_spec = GridSpec(
    id="BRAZIL/5km",
    type="local",
    crs="EPSG:5880",
    resolution=5000.0,
    bbox=[2336000.0, 6195000.0, 7120000.0, 10902000.0],
    description="Brazil PNLT Grid (5km)"
)
cube.register_grid(grid_spec)

# 2. Register Vector SpatialSources with the correct CRS (EPSG:5880)
rivers = SpatialSource(
    id="rios_pnlt",
    name="Rivers PNLT",
    format="vector",
    asset_url="data/raw/rios_pnlt/rios_pnlt_poly_sirgas2000.shp",
    crs="EPSG:5880"
)
cube.register_spatial_source(rivers)

urban = SpatialSource(
    id="urban_centers",
    name="Urban Centers",
    format="vector",
    asset_url="data/raw/urban_center/centros_urbanos_m_100_pnlt_poly_sirgas2000.shp",
    crs="EPSG:5880"
)
cube.register_spatial_source(urban)

# 3. Declare SpatialDerivation for Distances
derivation_rivers = SpatialDerivation(
    source_id="rios_pnlt",
    grid_id="BRAZIL/5km",
    role="driver",
    variables=[
        Variable(name="dist_rivers", operator="min_distance")
    ]
)

derivation_urban = SpatialDerivation(
    source_id="urban_centers",
    grid_id="BRAZIL/5km",
    role="driver",
    variables=[
        Variable(name="dist_urban", operator="min_distance")
    ]
)

# 4. Execute Pipelines
print("Calculating distance to rivers (Euclidean Distance Transform)...")
cube.derive(derivation_rivers)

print("Calculating distance to urban centers...")
cube.derive(derivation_urban)

# 5. Load and Verify
variables = ["dist_rivers", "dist_urban"]
print(f"Loading derived distances: {variables}")
backend = cube.to_lucc_data(variables)

for var in variables:
    arr = backend.get(var)
    # Distances are in meters because the grid is EPSG:29101 (metric)
    print(f"Variable '{var}': min={arr.min():.1f}m, max={arr.max()/1000:.1f}km, mean={arr.mean()/1000:.1f}km")

print("\nSuccess! Distance drivers are ready in the Cube.")
