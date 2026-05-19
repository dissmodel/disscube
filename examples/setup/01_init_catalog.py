"""
examples/setup/01_init_catalog.py

Bootstraps the DissCube catalog by registering the required simulation grids.
This is an idempotent operation.

Usage:
    python examples/setup/01_init_catalog.py
"""

from disscube.client import CubeClient
from disscube.models import GridSpec
from disscube.utils.grids import register_local_grid, register_simulation_grids

CATALOG_FILE = "catalog.db"
cube = CubeClient(catalog=CATALOG_FILE, store="./data/")

print("=== 1. Registering national simulation grids ===")
# Registers BR/5km and BR/1km (BDC Albers)
register_simulation_grids(cube)

print("\n=== 2. Registering local grids ===")

# Ilha do Maranhão (BDC Albers, snapped to 100m mesh)
register_local_grid(
    cube,
    name="ilha_maranhao",
    bbox_geo=(-44.42, -2.80, -44.02, -2.40),
    resolution=100.0,
    snap=True,
)

# Acre state grids (BDC Albers, snapped)
# Using the exact geographic bounds derived from data/raw/acre_sel.gpkg
acre_bbox = (-73.9868097, -11.1455615, -66.6235942, -7.1130573)

register_local_grid(
    cube,
    state="AC",
    bbox_geo=acre_bbox,
    resolution=5_000.0,
    snap=True,
)

register_local_grid(
    cube,
    state="AC",
    bbox_geo=acre_bbox,
    resolution=1_000.0,
    snap=True,
)

print("\n=== Catalog bootstrap complete ===")
