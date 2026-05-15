"""
examples/02_register_drivers.py

Derives spatial driver variables on BR/5km:
  - slope          → mean slope per cell         (raster, EPSG:5880)
  - presenca_ti    → indigenous land presence     (vector, EPSG:5880)
  - dist_cidades   → min distance to urban center (vector, EPSG:5880)
  - dist_rios      → min distance to rivers       (vector, EPSG:5880)

Prerequisites
-------------
01_setup_catalog.py must have been run first:
  - catalog.db exists
  - BR/5km is registered
  - slope_brazil, terras_indigenas, urban_centers and rios_pnlt are registered as
    SpatialSources (see _aux list in 01_setup_catalog.py)

Run:
    python examples/02_register_drivers.py
"""

from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable

GRID_ID = "BR/5km"

# ---------------------------------------------------------------------------
# Initialize client
# ---------------------------------------------------------------------------

cube = CubeClient(catalog="catalog.db", store="./data/")

# Sanity check — BR/5km must exist before deriving anything on it
grid = cube.catalog.get_grid(GRID_ID)
if grid is None:
    raise RuntimeError(
        f"Grid {GRID_ID!r} not found in catalog. "
        "Run 01_setup_catalog.py first."
    )
print(f"[ok] grid {GRID_ID}  {grid.rows} rows × {grid.cols} cols")

# ---------------------------------------------------------------------------
# 1. Slope — raster, mean aggregation
#
# Source CRS: EPSG:5880 (SIRGAS 2000 / Brazil Polyconic)
# GridAligner reprojects to BDC Albers at derive() time.
# ---------------------------------------------------------------------------

print("\n--- 1. Slope ---")

derivation_slope = SpatialDerivation(
    source_id="slope_brazil",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="slope", operator="mean"),
    ],
)
print(f"  [derive] spec_hash: {derivation_slope.spec_hash()}")
cube.derive(derivation_slope)
print("  [derive] slope done")

# ---------------------------------------------------------------------------
# 2. Terras Indígenas — vector, presence
#
# operator="presence" rasterizes polygon footprint (value=1, fill=0).
# ---------------------------------------------------------------------------

print("\n--- 2. Terras Indígenas ---")

derivation_ti = SpatialDerivation(
    source_id="terras_indigenas",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="presenca_ti", operator="presence"),
    ],
)
print(f"  [derive] spec_hash: {derivation_ti.spec_hash()}")
cube.derive(derivation_ti)
print("  [derive] presenca_ti done")

# ---------------------------------------------------------------------------
# 3. Distância a cidades — vector, min_distance
#
# operator="min_distance" computes Euclidean distance transform in metres.
# BDC Albers is in metres — no unit conversion needed.
# ---------------------------------------------------------------------------

print("\n--- 3. Distância a cidades ---")

derivation_dist = SpatialDerivation(
    source_id="urban_centers",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="dist_cidades", operator="min_distance"),
    ],
)
print(f"  [derive] spec_hash: {derivation_dist.spec_hash()}")
cube.derive(derivation_dist)
print("  [derive] dist_cidades done")

# ---------------------------------------------------------------------------
# 4. Distância a rios — vector, min_distance
#
# operator="min_distance" computes Euclidean distance transform in metres.
# ---------------------------------------------------------------------------

print("\n--- 4. Distância a rios ---")

derivation_rios = SpatialDerivation(
    source_id="rios_pnlt",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="dist_rios", operator="min_distance"),
    ],
)
print(f"  [derive] spec_hash: {derivation_rios.spec_hash()}")
cube.derive(derivation_rios)
print("  [derive] dist_rios done")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n=== Drivers ready ===")
results = cube.search(grid=GRID_ID, role="driver")
for r in results:
    print(f"  {r.name:20s}  hash={r.content_hash[:12] if r.content_hash else 'n/a'}  {r.asset_url}")