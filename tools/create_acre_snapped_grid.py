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
    print(f"Reading Acre boundaries from {GPKG_FILE}...")
    gdf = gpd.read_file(GPKG_FILE)
    
    # Ensure it's in EPSG:4326 for register_state_grid
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    bbox = gdf.total_bounds  # (minx, miny, maxx, maxy)
    print(f"Geographic BBox (EPSG:4326): {bbox}")

    # 3. Register snapped grid
    # register_local_grid will project to BDC Albers and snap to 5000m mesh
    register_local_grid(
        cube,
        name="AC",
        bbox_geo=tuple(bbox),
        resolution=5000.0,
        snap=True
    )

    print("\nGrid registration complete.")

if __name__ == "__main__":
    main()
