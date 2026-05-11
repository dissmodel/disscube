import rasterio
import sys

path = "./data/raw/decliv_sc_250_poly_sirgas2000.tif"
try:
    with rasterio.open(path) as src:
        print(f"File: {path}")
        print(f"CRS: {src.crs}")
        print(f"Bounds: {src.bounds}")
        print(f"Resolution: {src.res}")
        print(f"Width x Height: {src.width}x{src.height}")
        print(f"Dtype: {src.dtypes[0]}")
        print(f"Nodata: {src.nodata}")
except Exception as e:
    print(f"Error: {e}")
