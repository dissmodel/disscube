from disscube.models import GridSpec, SpatialSource
from disscube.client import CubeClient
import fiona
from shapely.geometry import shape

def import_bdc_grids(cube: CubeClient, sm_path: str, md_path: str, lg_path: str):
    """
    Imports BDC tiles as 'SpatialSources' linked to 3 master GridSpecs.
    """
    # BDC Albers Equal Area PROJ string
    bdc_crs = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
    
    # Brazil BBox in BDC Albers (approximate)
    brazil_bbox = [2850000, 7150000, 7250000, 11000000]

    grid_configs = [
        ('SM', sm_path, 10.0),   # 10m resolution
        ('MD', md_path, 30.0),   # 30m resolution
        ('LG', lg_path, 60.0),   # 60m resolution
        ('100m', lg_path, 100.0) # 100m custom resolution (using LG tiles as spatial reference)
    ]
    
    for label, path, resolution in grid_configs:
        grid_id = f"BDC_{label}"
        print(f"Registering master grid {grid_id}...")
        
        master_grid = GridSpec(
            id=grid_id,
            type="reference",
            crs=bdc_crs,
            resolution=resolution,
            bbox=brazil_bbox,
            description=f"BDC {label} Master Grid (Brazil)"
        )
        cube.register_grid(master_grid)

        print(f"Importing BDC_{label} tiles from {path} as sources...")
        with fiona.open(path) as src:
            for rec in src:
                tile_id = rec['properties']['tile']
                geom = shape(rec['geometry'])
                bbox = list(geom.bounds)
                
                # Create a SpatialSource for each tile
                source = SpatialSource(
                    id=f"{grid_id}_{tile_id}",
                    name=f"BDC {label} Tile {tile_id}",
                    format="raster",
                    asset_url=f"data/bdc/{label}/{tile_id}.tif",
                    crs=bdc_crs,
                    bbox=bbox
                )
                cube.register_spatial_source(source)
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
