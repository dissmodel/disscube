from disscube.client import CubeClient
import xarray as xr
import rioxarray
import os
import sys

# Initialize client
cube = CubeClient(catalog="catalog.db", store="./data/")

# 1. Search for Acre LUC data and Distance drivers in the catalog
results = cube.search(grid="AC/5km-métrica", role="luc_observation")
results += cube.search(grid="BRAZIL/5km", role="driver")

if not results:
    print("No data found in catalog.")
    sys.exit(1)

# Create output directory
output_dir = "outputs/brazil"
os.makedirs(output_dir, exist_ok=True)

print(f"Exporting variables...")

# 2. Export each derived variable to GeoTIFF
import geopandas as gpd
# Map of grid_id to default CRS for export fallback
GRID_CRS = {
    "AC/5km-métrica": "EPSG:29101",
    "BRAZIL/5km": "EPSG:5880"
}

for derived in results:
    output_tif = os.path.join(output_dir, f"{derived.name}.tif")
    
    print(f"  -> Converting {derived.name} (Grid: {derived.grid_id}) to {output_tif}...")
    try:
        ds = xr.open_zarr(derived.asset_url)
        da = ds[derived.name]
        
        # Determine CRS
        target_crs = GRID_CRS.get(derived.grid_id, "EPSG:4326")
        
        # Force the correct CRS
        da.rio.write_crs(target_crs, inplace=True)
            
        da.rio.to_raster(output_tif)
        print(f"     Saved successfully.")
    except Exception as e:
        print(f"     Error exporting {derived.name}: {e}")

print(f"\nDone! You can now open the TIFF files in '{output_dir}/' using QGIS.")
