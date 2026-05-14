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

    # 2. Register a Brazil 5km Grid aligned with BDC
    # BDC Albers Equal Area CRS
    # Expanded BBox to cover all Brazil and the slope data extent:
    # MinX: 2400000 (Slope starts at 2.49M)
    # MinY: 7100000 (BDC baseline)
    # MaxX: 7400000 (Slope ends at 7.32M)
    # MaxY: 12100000 (Slope ends at 12.03M)
    bdc_crs = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
    bdc_bbox = [2400000, 7100000, 7400000, 12100000]

    brazil_5km = GridSpec(
        id="BR/5km",
        type="local",
        crs=bdc_crs,
        resolution=5000.0,
        bbox=bdc_bbox,
        description="Brazil 5km Grid (Aligned with BDC Albers, Full Extent)"
    )
    cube.register_grid(brazil_5km)
    print(f"Registered grid: {brazil_5km.id} ({brazil_5km.rows}x{brazil_5km.cols})")

if __name__ == "__main__":
    main()
