import xarray as xr
import rioxarray
import os

zarr_path = "./data/derived/50c89f9c414256894434e197ffb5a461ffa7c39bb5cb743bab8b68eedd19d0ae/dist_sedes.zarr"
output_tif = "outputs/bdc_verification/dist_sedes_009002.tif"

os.makedirs(os.path.dirname(output_tif), exist_ok=True)

print(f"Opening Zarr: {zarr_path}")
ds = xr.open_zarr(zarr_path)
da = ds["dist_sedes"]

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
