from disscube.client import CubeClient
from disscube.models import GridSpec

def main():
    cube = CubeClient(catalog="catalog.db", store="./data/")
    
    # Get original grid
    orig = cube.catalog.get_grid("BDC_LG")
    if not orig:
        print("Original grid (BDC_LG) not found")
        return

    # Register 300m version
    new_grid = GridSpec(
        id="BDC_LG_300m",
        type="local",
        crs=orig.crs,
        resolution=300.0,
        bbox=orig.bbox,
        description="BDC LG Master Grid at 300m resolution"
    )
    cube.register_grid(new_grid)
    print(f"Registered {new_grid.id} with {new_grid.rows} rows and {new_grid.cols} cols")

if __name__ == "__main__":
    main()
