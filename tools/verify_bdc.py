import numpy as np
import rasterio
from rasterio.transform import from_origin
from disscube.client import CubeClient
import os

def generate_tile_tif(grid_id, cube, output_path):
    grid = cube.catalog.get_grid(grid_id)
    if not grid:
        print(f"Grid {grid_id} not found!")
        return

    # Use a coarse resolution for verification (1km) to avoid huge files
    res = 1000.0 
    width = int((grid.bbox[2] - grid.bbox[0]) / res)
    height = int((grid.bbox[3] - grid.bbox[1]) / res)
    
    transform = from_origin(grid.bbox[0], grid.bbox[3], res, res)
    
    # Create a simple pattern (border + cross)
    data = np.zeros((height, width), dtype=np.uint8)
    data[0, :] = 255
    data[-1, :] = 255
    data[:, 0] = 255
    data[:, -1] = 255
    data[height//2, :] = 127
    data[:, width//2] = 127

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Use explicit PROJ string for Albers BDC since EPSG:200000 might not be in the proj db
    bdc_proj = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
    
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=data.dtype,
        crs=bdc_proj,
        transform=transform,
    ) as dst:
        dst.write(data, 1)
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    cube = CubeClient(catalog="catalog.db", store="./data/")
    
    # Selected master grids for verification:
    tiles = [
        "BDC_LG",
        "BDC_MD",
        "BDC_SM"
    ]
    
    for t in tiles:
        generate_tile_tif(t, cube, f"outputs/bdc_verification/{t}.tif")
