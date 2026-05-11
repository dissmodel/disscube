import fiona
import os

path = "zip://data/raw/terras_indigenas_funai_2010_limpo_poly_sirgas2000.zip"
try:
    with fiona.open(path) as src:
        print(f"File: {path}")
        print(f"CRS: {src.crs}")
        print(f"Bounds: {src.bounds}")
        print(f"Schema: {src.schema}")
        print(f"Count: {len(src)}")
except Exception as e:
    print(f"Error: {e}")
