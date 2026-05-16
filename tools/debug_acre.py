import geopandas as gpd
import pyproj
from shapely.geometry import box
import os

bdc_crs = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
grid_bbox = [2400000, 7100000, 7400000, 12100000]
grid_geom = box(*grid_bbox)

def check_acre():
    path = "data/raw/acre_data.zip"
    if not os.path.exists(path):
        print(f"File {path} not found.")
        return

    gdf = gpd.read_file(path)
    print(f"Original CRS: {gdf.crs}")
    print(f"Original Bounds: {gdf.total_bounds}")

    # If coords are negative, maybe they lack the false easting/northing
    # EPSG:29101 has +x_0=5000000 +y_0=10000000
    # Let's try to add them manually if bounds are around -1.8M
    if gdf.total_bounds[0] < 0:
        print("Negative coordinates detected. Attempting to add false easting/northing (5M, 10M)...")
        gdf.geometry = gdf.geometry.translate(xoff=5000000, yoff=10000000)
        print(f"New Bounds: {gdf.total_bounds}")

    # Now try to reproject to BDC
    try:
        # We need to tell geopandas what the CRS is after translation if we want to reproject
        # but translation doesn't change the CRS definition, just the numbers.
        # If the numbers now match EPSG:29101 definition:
        gdf.crs = "+proj=poly +lat_0=0 +lon_0=-54 +x_0=5000000 +y_0=10000000 +ellps=aust_SA +units=m +no_defs"
        gdf_bdc = gdf.to_crs(bdc_crs)
        print(f"Bounds in BDC: {gdf_bdc.total_bounds}")
        print(f"Intersects Grid? {gdf_bdc.intersects(grid_geom).any()}")
    except Exception as e:
        print(f"Reprojection error: {e}")

if __name__ == "__main__":
    check_acre()
