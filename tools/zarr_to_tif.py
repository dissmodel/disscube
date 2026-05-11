from disscube.client import CubeClient
import xarray as xr
import rioxarray
import os
import sys

# Initialize client to find the derived variable
cube = CubeClient(catalog="catalog.json", store="./data/")

# Search for the specific variable
variable_name = "dist_sedes"
grid_id = "BDC_LG_009002_60m"
derived = cube.search(grid=grid_id, role="driver")
target_var = next((d for d in derived if d.name == variable_name), None)

if not target_var:
    print(f"Error: Variable '{variable_name}' for grid '{grid_id}' not found in catalog.")
    sys.exit(1)

zarr_path = target_var.asset_url
output_tif = f"outputs/bdc_verification/dist_sedes_{grid_id}.tif"

os.makedirs(os.path.dirname(output_tif), exist_ok=True)

print(f"Opening Zarr: {zarr_path}")
ds = xr.open_zarr(zarr_path)
da = ds[variable_name]

# Explicit PROJ string for BDC Albers
bdc_proj = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
da.rio.write_crs(bdc_proj, inplace=True)

print(f"Exporting to TIF: {output_tif}")
da.rio.to_raster(output_tif)
print("Done.")
