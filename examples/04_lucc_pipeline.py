import os
import geopandas as gpd
from disscube.client import CubeClient
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable

cube = CubeClient(catalog="catalog.db", store="./data/")

# 1. Use BR/5km as reference grid (National, BDC Albers)
grid_id = "BR/5km"

# 2. Register Source
proj_acre = "+proj=poly +lat_0=0 +lon_0=-54 +x_0=0 +y_0=0 +ellps=aust_SA +units=m +no_defs"

asset_path = "data/raw/acre_data.zip"
if not os.path.exists(asset_path):
    asset_path = "../disslucc-continuous/examples/data/input/csAC.zip"

# Pre-processing step: Convert to 4326 to ensure stable reprojection to Albers later
temp_file = "data/raw/acre_4326.json"
if not os.path.exists(temp_file):
    print("Pre-processing Acre data to EPSG:4326 for better alignment...")
    gdf = gpd.read_file(asset_path)
    gdf.crs = proj_acre
    gdf = gdf.to_crs("EPSG:4326")
    gdf.to_file(temp_file, driver="GeoJSON")

data_source = SpatialSource(
    id="acre_base_bdc_global",
    name="Acre Vector Data (Global BDC)",
    format="vector",
    asset_url=temp_file,
    crs="EPSG:4326"
)
cube.register_spatial_source(data_source)

# 3. Process Global (All Acre in one go)
variables_spec = [
    Variable(name="f", operator="attribute"),
    Variable(name="d", operator="attribute")
]

print(f"\n>>> Processing Acre Global for {grid_id}...")
derivation = SpatialDerivation(
    source_id="acre_base_bdc_global",
    grid_id=grid_id,
    role="luc_observation",
    variables=variables_spec
)

try:
    # No tile_id means process the whole grid extent
    cube.derive(derivation)
    print(f"Success!")
    
    # Load and check
    da_f = cube.load("f", grid_id=grid_id)
    # Filter only where we have data for mean calculation
    valid_data = da_f.where(da_f > 0)
    mean_val = valid_data.mean().values
    print(f"Global variable 'f' mean (excluding zeros): {mean_val:.4f}")
    print(f"Result saved at: {cube.search(grid=grid_id, role='luc_observation')[0].asset_url}")
except Exception as e:
    print(f"Error: {e}")

print("\nAcre LUCC Global Pipeline Finished.")
