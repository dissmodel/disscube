from disscube.client import CubeClient
from disscube.models import GridSpec

def main():
    cube = CubeClient(catalog="catalog.json", store="./data/")
    
    # Get original grid
    orig = cube.catalog.get_grid("BDC_LG_009002")
    if not orig:
        print("Original grid not found")
        return

    # Register 60m version
    new_grid = GridSpec(
        id="BDC_LG_009002_60m",
        type="local",
        crs=orig.crs,
        resolution=60.0,
        bbox=orig.bbox,
        description="BDC LG 009002 at 60m resolution"
    )
    cube.register_grid(new_grid)
    print(f"Registered {new_grid.id} with {new_grid.rows} rows and {new_grid.cols} cols")

if __name__ == "__main__":
    main()
