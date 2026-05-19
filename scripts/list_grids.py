from disscube.client import CubeClient
cube = CubeClient(catalog="catalog.db", store="./data/")
for grid in cube.catalog.list_grids():
    print(f"Grid: {grid.id}")
    print(f"  CRS: {grid.crs}")
    print(f"  BBox: {grid.bbox}")
    print(f"  Res: {grid.resolution}")
