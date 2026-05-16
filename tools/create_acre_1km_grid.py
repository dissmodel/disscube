import os
import geopandas as gpd
from disscube.client import CubeClient
from disscube.utils.grids import register_local_grid

CATALOG_FILE = "catalog.db"
GPKG_FILE = "data/raw/acre_sel.gpkg"

def main():
    if not os.path.exists(GPKG_FILE):
        print(f"Error: {GPKG_FILE} not found.")
        return

    # 1. Initialize client
    cube = CubeClient(catalog=CATALOG_FILE, store="./data/")

    # 2. Read Acre boundaries and get geographic bbox
    gdf = gpd.read_file(GPKG_FILE)
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    bbox = gdf.total_bounds

    # 3. Register snapped grid at 1km resolution
    register_local_grid(
        cube,
        name="AC",
        bbox_geo=tuple(bbox),
        resolution=1000.0,
        snap=True
    )

    print("\nGrade de 1km registrada.")

if __name__ == "__main__":
    main()
