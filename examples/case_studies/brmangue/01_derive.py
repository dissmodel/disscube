"""
examples/case_studies/brmangue/01_derive.py

BR-MANGUE case study — Derivation of land use variables for Ilha do Maranhão (ilha_maranhao/100m).

Usage:
    python examples/case_studies/brmangue/01_derive.py
"""

from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable


GRID_ID   = "ilha_maranhao/100m"
SOURCE_ID = "maranhao_base"
cube = CubeClient(catalog="catalog.db", store="./data/")

# Sanity checks
if not cube.catalog.get_grid(GRID_ID):
    raise RuntimeError(f"Grid {GRID_ID!r} not found. Run examples/setup/01_init_catalog.py first.")
if not cube.catalog.get_spatial_source(SOURCE_ID):
    raise RuntimeError(f"Source {SOURCE_ID!r} not found. Run examples/setup/02_register_sources.py first.")

# Derivation — uso, alt, solo from maranhao_base raster
print(f"\n[derive] Processing {SOURCE_ID} @ {GRID_ID}...")
cube.derive(SpatialDerivation(
    source_id=SOURCE_ID,
    grid_id=GRID_ID,
    role="luc_observation",
    variables=[
        Variable(name="uso",  operator="majority"),
        Variable(name="alt",  operator="mean"),
        Variable(name="solo", operator="majority"),
    ],
))

print("\n=== BR-MANGUE derivation complete ===")
