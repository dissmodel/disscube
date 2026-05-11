import fiona
from shapely.geometry import shape
from disscube.models import GridSpec
from disscube.client import CubeClient

def import_bdc_grids(cube: CubeClient, sm_path: str, md_path: str, lg_path: str):
    """
    Imports BDC tiles from shapefiles as 'reference' GridSpecs.
    The resolution for BDC reference grids is the tile size in meters.
    """
    # BDC Albers Equal Area PROJ string
    bdc_crs = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
    
    grid_configs = [
        ('SM', sm_path, 105600.0),   # Tile size for Small
        ('MD', md_path, 211200.0),   # Tile size for Medium
        ('LG', lg_path, 422400.0)    # Tile size for Large
    ]
    
    for label, path, tile_size in grid_configs:
        print(f"Importing BDC_{label} grids from {path}...")
        with fiona.open(path) as src:
            for rec in src:
                tile_id = rec['properties']['tile']
                geom = shape(rec['geometry'])
                bbox = list(geom.bounds)
                
                grid = GridSpec(
                    id=f"BDC_{label}_{tile_id}",
                    type="reference",
                    crs=bdc_crs,
                    resolution=tile_size,
                    bbox=bbox,
                    description=f"BDC {label} Grid Tile {tile_id}"
                )
                cube.register_grid(grid)
        print(f"Finished BDC_{label}")

if __name__ == "__main__":
    import os
    # Use the default catalog.json in the current dir
    cube = CubeClient(catalog="catalog.json", store="./data/")
    import_bdc_grids(
        cube,
        "/tmp/bdc_grids/SM/BDC_SM_V2.shp",
        "/tmp/bdc_grids/MD/BDC_MD_V2.shp",
        "/tmp/bdc_grids/LG/BDC_LG_V2.shp"
    )
