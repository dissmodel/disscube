"""
examples/02_register_drivers.py

Registers auxiliary driver sources and derives spatial variables on BR/5km:
  - slope_brazil      → mean slope per cell (raster, EPSG:5880)
  - terras_indigenas  → indigenous land presence per cell (vector, EPSG:5880)
  - urban_centers     → minimum distance to urban centers per cell (vector, EPSG:5880)

Assumes 01_setup_catalog.py has already been run (catalog.db exists and
BR/5km is registered with the correct bbox).

Run:
    python examples/02_register_drivers.py
"""

from disscube.client import CubeClient
from disscube.models import SpatialSource, SpatialDerivation, Variable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BDC_CRS = (
    "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22"
    " +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
)

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
# GridAligner will reproject to BDC Albers at derive() time.
# Bounds from raster inspection:
#   [2_662_311, 6_038_008, 7_171_061, 10_708_008]  (EPSG:5880)
# ---------------------------------------------------------------------------

print("\n--- 1. Slope ---")

cube.register_spatial_source(SpatialSource(
    id="slope_brazil",
    name="Brazil Slope 250 m",
    format="raster",
    asset_url="data/raw/decliv_sc_250_poly_sirgas2000.tif",
    crs="EPSG:5880",
))
print("  [source] slope_brazil registered")

derivation_slope = SpatialDerivation(
    source_id="slope_brazil",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="slope", operator="mean"),
    ],
)
print(f"  [derive] spec_hash: {derivation_slope.spec_hash()}")
print("  [derive] running pipeline …")
cube.derive(derivation_slope)
print("  [derive] slope done")

# ---------------------------------------------------------------------------
# 2. Terras Indígenas — vector, presence
#
# Source CRS: EPSG:5880
# operator="presence" rasterizes polygon footprint (value=1, fill=0).
# ---------------------------------------------------------------------------

print("\n--- 2. Terras Indígenas ---")

cube.register_spatial_source(SpatialSource(
    id="terras_indigenas",
    name="Terras Indígenas FUNAI 2010",
    format="vector",
    asset_url="zip://data/raw/terras_indigenas_funai_2010_limpo_poly_sirgas2000.zip",
    crs="EPSG:5880",
))
print("  [source] terras_indigenas registered")

derivation_ti = SpatialDerivation(
    source_id="terras_indigenas",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="presenca_ti", operator="presence"),
    ],
)
print(f"  [derive] spec_hash: {derivation_ti.spec_hash()}")
print("  [derive] running pipeline …")
cube.derive(derivation_ti)
print("  [derive] presenca_ti done")

# ---------------------------------------------------------------------------
# 3. Distância a cidades — vector, min_distance
#
# Source CRS: EPSG:5880
# operator="min_distance" computes Euclidean distance transform in metres.
# Result unit: metres (BDC Albers is in metres, so no unit conversion needed).
# ---------------------------------------------------------------------------

print("\n--- 3. Distância a cidades ---")

cube.register_spatial_source(SpatialSource(
    id="urban_centers",
    name="Urban Centers (PNLT)",
    format="vector",
    asset_url="data/raw/urban_center/centros_urbanos_m_100_pnlt_poly_sirgas2000.shp",
    crs="EPSG:5880",
))
print("  [source] urban_centers registered")

derivation_dist = SpatialDerivation(
    source_id="urban_centers",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="dist_cidades", operator="min_distance"),
    ],
)
print(f"  [derive] spec_hash: {derivation_dist.spec_hash()}")
print("  [derive] running pipeline …")
cube.derive(derivation_dist)
print("  [derive] dist_cidades done")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n=== Drivers ready ===")
results = cube.search(grid=GRID_ID, role="driver")
for r in results:
    print(f"  {r.name:20s}  hash={r.content_hash[:12] if r.content_hash else 'n/a'}  {r.asset_url}")
