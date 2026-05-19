"""
examples/setup/02_register_sources.py

Registers raw data sources (SpatialSources) into the catalog.
This script copies data from external research folders if available.

Usage:
    python examples/setup/02_register_sources.py
"""

import os
import shutil
from disscube.client import CubeClient
from disscube.models import SpatialSource

# ── 1. Path & Copy Utilities ──────────────────────────────────────────────────

def copy_if_exists(src: str, dst: str) -> bool:
    """Helper to copy raw data from external research folders."""
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
        print(f"  [copy] {src} → {dst}")
        return True
    return False

def check_path(url: str) -> str:
    """Strip protocol prefixes for local filesystem checks."""
    for prefix in ("zip://", "file://"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return url

# ── 2. Source Definitions ───────────────────────────────────────────────────

# Map of standard sources used in examples
# Format: id -> {name, url, format, crs, [time]}
STANDARD_SOURCES = {
    "maranhao_base": {
        "name": "Ilha do Maranhão — raster EPSG:31983",
        "url": "data/raw/ilha_maranhao.tif",
        "format": "raster",
        "crs": "EPSG:31983",
    },
    "acre_base": {
        "name": "Acre — vector EPSG:4326",
        "url": "data/raw/acre_data.zip",
        "format": "vector",
        "crs": "EPSG:4326",
    },
    "slope_brazil": {
        "name": "Brazil Slope 250 m",
        "url": "data/raw/decliv_sc_250_poly_sirgas2000.tif",
        "format": "raster",
        "crs": "EPSG:5880",
    },
    "terras_indigenas": {
        "name": "Terras Indígenas FUNAI 2010",
        "url": "zip://data/raw/terras_indigenas_funai_2010_limpo_poly_sirgas2000.zip",
        "format": "vector",
        "crs": "EPSG:5880",
    },
    "urban_centers": {
        "name": "Urban Centers (PNLT)",
        "url": "data/raw/urban_center/centros_urbanos_m_100_pnlt_poly_sirgas2000.shp",
        "format": "vector",
        "crs": "EPSG:5880",
    },
    "rios_pnlt": {
        "name": "Rivers PNLT",
        "url": "data/raw/rios_pnlt/rios_pnlt_poly_sirgas2000.shp",
        "format": "vector",
        "crs": "EPSG:5880",
    },
}

# ── 3. Main Execution ───────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1. External research folders (adjust to your local environment)
    BRMANGUE_SRC = "../brmangue-dissmodel/examples/data/input/ilha_maranhao_epsg31983.tif"
    ACRE_SRC     = "../disslucc-continuous/examples/data/input/csAC.zip"

    BRMANGUE_DST = "data/raw/ilha_maranhao.tif"
    ACRE_DST     = "data/raw/acre_data.zip"

    print("=== 1. Copying raw data (if available) ===")
    copy_if_exists(BRMANGUE_SRC, BRMANGUE_DST)
    copy_if_exists(ACRE_SRC,     ACRE_DST)

    # 2. Register Sources
    cube = CubeClient(catalog="catalog.db", store="./data/")
    
    print("\n=== 2. Registering standard spatial sources ===")
    for src_id, meta in STANDARD_SOURCES.items():
        local_path = check_path(meta["url"])
        
        if os.path.exists(local_path):
            source = SpatialSource(
                id=src_id,
                name=meta["name"],
                format=meta["format"],
                asset_url=meta["url"],
                crs=meta["crs"],
                time=meta.get("time"),
            )
            cube.register_spatial_source(source)
            print(f"  [source] {src_id} registered")
        else:
            print(f"  [warn]   {src_id} skipped (file not found: {local_path})")

    print("\n=== Registration complete ===")
