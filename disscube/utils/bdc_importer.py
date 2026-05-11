import fiona
from shapely.geometry import shape
from disscube.models import GridSpec
from disscube.client import CubeClient

def import_bdc_grids(cube: CubeClient, sm_path: str, md_path: str, lg_path: str):
    """
    Imports BDC tiles from shapefiles as 'reference' GridSpecs.
    """
    grid_configs = [
        ('SM', sm_path, 10.0),
        ('MD', md_path, 20.0),
        ('LG', lg_path, 60.0)
    ]
    
    for label, path, default_res in grid_configs:
        print(f"Importing BDC_{label} grids from {path}...")
        with fiona.open(path) as src:
            for rec in src:
                tile_id = rec['properties']['tile']
                geom = shape(rec['geometry'])
                bbox = list(geom.bounds)
                
                grid = GridSpec(
                    id=f"BDC_{label}_{tile_id}",
                    type="reference",
                    crs="EPSG:200000",
                    resolution=default_res,
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
