from disscube.client import CubeClient
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable
import os

cube = CubeClient(catalog="catalog.db", store="./data/")

grid_id = "BR/5km"

# 1. Register Vector SpatialSources
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

# 2. Declare SpatialDerivation for Distances
derivation_rivers = SpatialDerivation(
    source_id="rios_pnlt",
    grid_id=grid_id,
    role="driver",
    variables=[
        Variable(name="dist_rivers", operator="min_distance")
    ]
)

derivation_urban = SpatialDerivation(
    source_id="urban_centers",
    grid_id=grid_id,
    role="driver",
    variables=[
        Variable(name="dist_urban", operator="min_distance")
    ]
)

# 3. Execute Pipelines
print(f"Calculating distance to rivers for {grid_id}...")
cube.derive(derivation_rivers)

print(f"Calculating distance to urban centers for {grid_id}...")
cube.derive(derivation_urban)

# 4. Load and Verify
variables = ["dist_rivers", "dist_urban"]
print(f"Loading derived distances: {variables}")
backend = cube.to_lucc_data(variables)

for var in variables:
    arr = backend.get(var)
    print(f"Variable '{var}': min={arr.min():.1f}m, max={arr.max()/1000:.1f}km, mean={arr.mean()/1000:.1f}km")

print("\nSuccess! Distance drivers are ready in the Cube.")
