"""
examples/case_studies/lucc_acre/01_derive.py

LUCC case study — Derivation of land use attributes for Acre (AC/5km).

Usage:
    python examples/case_studies/lucc_acre/01_derive.py
"""

from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable

GRID_ID   = "AC/5km"
SOURCE_ID = "acre_base"
cube = CubeClient(catalog="catalog.db", store="./data/")

# Sanity checks
if not cube.catalog.get_grid(GRID_ID):
    raise RuntimeError(f"Grid {GRID_ID!r} not found. Run examples/setup/01_init_catalog.py first.")
if not cube.catalog.get_spatial_source(SOURCE_ID):
    raise RuntimeError(f"Source {SOURCE_ID!r} not found. Run examples/setup/02_register_sources.py first.")

# Derivation — land use class attributes f and d
print(f"\n[derive] Processing {SOURCE_ID} @ {GRID_ID}...")
cube.derive(SpatialDerivation(
    source_id=SOURCE_ID,
    grid_id=GRID_ID,
    role="luc_observation",
    variables=[
        Variable(name="f", operator="attribute"),
        Variable(name="d", operator="attribute"),
    ],
))

print("\n=== LUCC Acre derivation complete ===")
