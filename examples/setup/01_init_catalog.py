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

# Acre state grid (BDC Albers, snapped to 5km mesh)
register_local_grid(
    cube,
    name="AC",
    bbox_geo=(-74.0, -11.2, -66.5, -7.1),
    resolution=5_000.0,
)

# Acre state grid (BDC Albers, snapped to 1km mesh)
register_local_grid(
    cube,
    name="AC",
    bbox_geo=(-74.0, -11.2, -66.5, -7.1),
    resolution=1_000.0,
)

print("\n=== Catalog bootstrap complete ===")
