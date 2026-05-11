from disscube.client import CubeClient
import xarray as xr
import rioxarray
import os
import sys

# Initialize client to find the derived variable
cube = CubeClient(catalog="catalog.json", store="./data/")

# Search for the specific variable
variable_name = "dist_sedes"
derived = cube.search(grid="BDC_LG_009002", role="driver")
target_var = next((d for d in derived if d.name == variable_name), None)

if not target_var:
    print(f"Error: Variable '{variable_name}' not found in catalog.")
    sys.exit(1)

zarr_path = target_var.asset_url
output_tif = "outputs/bdc_verification/dist_sedes_009002.tif"

os.makedirs(os.path.dirname(output_tif), exist_ok=True)

print(f"Opening Zarr: {zarr_path}")
ds = xr.open_zarr(zarr_path)
da = ds[variable_name]

# Explicit PROJ string for BDC Albers
bdc_proj = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
da.rio.write_crs(bdc_proj, inplace=True)

print(f"Exporting to TIF: {output_tif}")
# Coarsen if too large (LG is large, 422km at 60m resolution would be ~7000x7000)
# But here we used 60m resolution from LG grid definition in importer.
# LG 009002 bbox is 6425600.0, 10264000.0, 6848000.0, 10686400.0 -> 422.4km
# At 60m -> 7040 pixels. 

da.rio.to_raster(output_tif)
print("Done.")
