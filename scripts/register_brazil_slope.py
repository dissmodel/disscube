from disscube.client import CubeClient
from disscube.models import GridSpec, SpatialSource

def main():
    cube = CubeClient(catalog="catalog.db", store="./data/")
    
    # 1. Register the Slope Raster Source
    # Metadata from tools/inspect_raster.py:
    # CRS: EPSG:5880
    # Bounds: [2662311.5057094283, 6038008.507941578, 7171061.505653188, 10708008.507883325]
    slope_source = SpatialSource(
        id="slope_brazil",
        name="Brazil Slope 250m",
        format="raster",
        asset_url="data/raw/decliv_sc_250_poly_sirgas2000.tif",
        crs="EPSG:5880"
    )
    cube.register_spatial_source(slope_source)
    print(f"Registered source: {slope_source.id}")

    # 2. Register a Brazil 5km Grid
    # We'll use the extent of the slope data but rounded to 5km alignment in EPSG:5880
    # MinX: 2660000, MinY: 6035000, MaxX: 7175000, MaxY: 10710000
    brazil_5km = GridSpec(
        id="BR/5km",
        type="local",
        crs="EPSG:5880",
        resolution=5000.0,
        bbox=[2660000.0, 6035000.0, 7175000.0, 10710000.0],
        description="Brazil 5km Grid (SIRGAS 2000 / Brazil Polyconic)"
    )
    cube.register_grid(brazil_5km)
    print(f"Registered grid: {brazil_5km.id} ({brazil_5km.rows}x{brazil_5km.cols})")

if __name__ == "__main__":
    main()
