import os
import shutil
from disscube.client import CubeClient
from disscube.models import GridSpec, DataSource, SpatialDerivation, Variable

# 1. Setup paths
CUBE_ROOT = os.getcwd()
DATA_DIR = os.path.join(CUBE_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# Sources from other repos
BRMANGUE_DATA = "../brmangue-dissmodel/examples/data/input/ilha_maranhao_epsg31983.tif"
ACRE_DATA = "../disslucc-continuous/examples/data/input/csAC.zip"

# Copy to our local raw data folder for the example
if os.path.exists(BRMANGUE_DATA):
    shutil.copy(BRMANGUE_DATA, os.path.join(RAW_DIR, "ilha_maranhao.tif"))
    print("Copied Maranhão TIFF")

if os.path.exists(ACRE_DATA):
    shutil.copy(ACRE_DATA, os.path.join(RAW_DIR, "acre_data.zip"))
    print("Copied Acre Vector (zip)")

# 2. Initialize Cube
cube = CubeClient(catalog="catalog.json", store="./data/")

# 3. Register Grids
# Acre Grid (matching disslucc resolution approx)
cube.register_grid(GridSpec(
    id="AC/0.01deg",
    type="local",
    crs="EPSG:4326",
    resolution=0.01,
    bbox=[-74.0, -11.5, -66.5, -7.0],
    description="Acre Grid"
))

# Maranhão Grid (High res 30m)
cube.register_grid(GridSpec(
    id="MA/30m",
    type="local",
    crs="EPSG:31983",
    resolution=30.0,
    bbox=[580000, 9700000, 600000, 9720000], # Approximate
    description="São Luís Grid"
))

# 4. Register DataSources
cube.register_source(DataSource(
    id="maranhao_base",
    name="Maranhao TIFF",
    format="raster",
    asset_url="data/raw/ilha_maranhao.tif",
    crs="EPSG:31983"
))

cube.register_source(DataSource(
    id="acre_base",
    name="Acre Vector",
    format="vector",
    asset_url="data/raw/acre_data.zip",
    crs="EPSG:4326"
))

print("\nCatalog prepared with existing data from ecosystem.")

# 5. Example Derivation (Declarative)
acre_roads_derivation = SpatialDerivation(
    source_id="acre_base",
    grid_id="AC/0.01deg",
    role="driver",
    variables=[
        Variable(name="dist_roads", operator="min_distance")
    ]
)

print(f"To test derivation, run:")
print(f"cube.derive(acre_roads_derivation)")
