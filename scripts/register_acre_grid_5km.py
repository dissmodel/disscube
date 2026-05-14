from disscube.models import GridSpec
from disscube.client import CubeClient
import pyproj
import os

def register_acre_grid():
    # BDC Albers Equal Area CRS
    bdc_crs = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
    
    # BDC ALIGNED BBOX
    # Based on Tile 005015 (minx=3152000, miny=10264000)
    # The grid has offsets: X_offset = 2000, Y_offset = 4000
    # We snap the real Acre bounds (2822427, 10053219, 3635851, 10471597) to these offsets
    
    bbox = [
        2822000.0,  # 2820000 + 2000 (X_offset)
        10049000.0, # 10045000 + 4000 (Y_offset)
        3637000.0,  # Snapped end
        10474000.0  # Snapped end
    ]
    resolution = 5000.0
    
    grid = GridSpec(
        id="BR/5km",
        type="reference",
        crs=bdc_crs,
        resolution=resolution,
        bbox=bbox,
        description="Acre grid PERFECTLY ALIGNED with BDC pixel grid (2000m/4000m offset)"
    )
    
    client = CubeClient(catalog="catalog.db", store="./data/")
    print(f"Registering GridSpec: {grid.id}")
    client.register_grid(grid)
    
    # Export to TOML
    toml_path = "dissmodel-configs/grids/acre_5km.toml"
    os.makedirs(os.path.dirname(toml_path), exist_ok=True)
    with open(toml_path, "w") as f:
        f.write(grid.to_toml())
    print(f"GridSpec exported to {toml_path}")
    
    # Final Summary for validation
    print("-" * 30)
    print(f"X range: {grid.bbox[0]} to {grid.bbox[2]} (Aligned: {grid.bbox[0] % 5000 == 2000})")
    print(f"Y range: {grid.bbox[1]} to {grid.bbox[3]} (Aligned: {grid.bbox[1] % 5000 == 4000})")
    print(f"Dimensions: {grid.rows}x{grid.cols}")

if __name__ == "__main__":
    register_acre_grid()
