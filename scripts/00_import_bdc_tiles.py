"""
scripts/00_import_bdc_tiles.py

Imports BDC tile shapefiles (SM / MD / LG) as SpatialSources into the catalog.

Run ONCE after 01_setup_catalog.py. No need to re-run unless the BDC
shapefiles change version.

    python scripts/00_import_bdc_tiles.py

Prerequisites
-------------
- catalog.db must exist (run 01_setup_catalog.py first)
- BDC shapefiles in data/bdc_grids/:
    data/bdc_grids/BDC_SM_V2.zip
    data/bdc_grids/BDC_MD_V2.zip
    data/bdc_grids/BDC_LG_V2.zip
"""

from disscube.client import CubeClient
from disscube.utils.bdc_importer import import_bdc_grids

CATALOG_FILE = "catalog.db"

cube = CubeClient(catalog=CATALOG_FILE, store="./data/")

print("=== Importing BDC tile sources (one-time, slow) ===")
import_bdc_grids(
    cube,
    sm_path="zip://data/bdc_grids/BDC_SM_V2.zip",
    md_path="zip://data/bdc_grids/BDC_MD_V2.zip",
    lg_path="zip://data/bdc_grids/BDC_LG_V2.zip",
)
print("\n=== BDC tiles registered ===")
