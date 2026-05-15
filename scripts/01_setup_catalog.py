"""
examples/01_setup_catalog.py

Prepares the DissCube catalog for the two reference cases:
  - BR-MANGUE  (coastal dynamics, Maranhão, raster input, 100 m)
  - LUCC/AC    (land use change, Acre, vector input, 5 km)

Run once before any pipeline script:

    python examples/01_setup_catalog.py

Prerequisites
-------------
- BR-MANGUE data in ../brmangue-dissmodel/examples/data/input/
- LUCC/AC data in  ../disslucc-continuous/examples/data/input/
- BDC grid shapefiles in data/bdc_grids/ (SM, MD, LG zips)
"""

import os
import shutil

from disscube.client import CubeClient
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable
from disscube.utils.bdc_importer import import_bdc_grids, register_state_grid

# ---------------------------------------------------------------------------
# 1. Paths
# ---------------------------------------------------------------------------

CUBE_ROOT = os.getcwd()
DATA_DIR  = os.path.join(CUBE_ROOT, "data")
RAW_DIR   = os.path.join(DATA_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)

BRMANGUE_SRC = "../brmangue-dissmodel/examples/data/input/ilha_maranhao_epsg31983.tif"
ACRE_SRC     = "../disslucc-continuous/examples/data/input/csAC.zip"

BRMANGUE_DST = os.path.join(RAW_DIR, "ilha_maranhao.tif")
ACRE_DST     = os.path.join(RAW_DIR, "acre_data.zip")


def _copy_if_exists(src: str, dst: str) -> bool:
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"  copied {src} → {dst}")
        return True
    print(f"  [warn] source not found, skipping: {src}")
    return False


print("=== 1. Copying raw data ===")
_copy_if_exists(BRMANGUE_SRC, BRMANGUE_DST)
_copy_if_exists(ACRE_SRC,     ACRE_DST)

# ---------------------------------------------------------------------------
# 2. Initialize catalog (fresh)
# ---------------------------------------------------------------------------

CATALOG_FILE = "catalog.db"

cube = CubeClient(catalog=CATALOG_FILE, store="./data/")

# ---------------------------------------------------------------------------
# 3. Register simulation grids
#
# GridSpec.resolution = pixel size of the DERIVED PRODUCT (model output).
# Has nothing to do with native satellite sensor resolution.
#
# National grids use BDC Albers (metres).
# AC/5km and MA/100m are local grids in the same or a compatible CRS.
#
# AC/0.01deg is NOT used: mixing geographic degrees with a metre-based
# pipeline causes silent errors in rows/cols/transform calculations.
# ---------------------------------------------------------------------------

print("\n=== 3. Registering simulation grids ===")

BDC_CRS     = ("+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22"
               " +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs")
BRAZIL_BBOX = [2_400_000.0, 7_100_000.0, 8_200_000.0, 12_100_000.0]

# National grids (BDC Albers, type="reference")
for grid_id, res, desc in [
    ("BR/5km",  5_000.0, "Grade nacional — 5 km, BDC Albers"),
    ("BR/1km",  1_000.0, "Grade nacional — 1 km, BDC Albers"),
    ("BR/100m",   100.0, "Grade nacional — 100 m, BDC Albers"),
]:
    g = GridSpec(
        id=grid_id,
        type="reference",
        crs=BDC_CRS,
        resolution=res,
        bbox=BRAZIL_BBOX,
        description=desc,
    )
    cube.register_grid(g)
    print(f"  [grid] {grid_id:12s}  {g.rows} rows × {g.cols} cols")

# Maranhão local grid — 100 m pixels, SIRGAS 2000 / UTM zone 23S
# bbox covers Ilha do Maranhão; refine after inspecting the actual TIFF
cube.register_grid(GridSpec(
    id="MA/100m",
    type="local",
    crs="EPSG:31983",
    resolution=100.0,
    bbox=[490_000.0, 9_680_000.0, 590_000.0, 9_760_000.0],
    description="Ilha do Maranhão — 100 m pixels, SIRGAS 2000 / UTM 23S",
))
print(f"  [grid] MA/100m       (local, UTM 23S)")

# Acre state grid — 5 km pixels, BDC Albers, snapped to national 5 km mesh.
# register_state_grid reprojects the geographic bbox to BDC Albers and
# snaps minx/miny/maxx/maxy to the nearest multiple of 5000 m.
register_state_grid(
    cube,
    state="AC",
    bbox_geo=(-74.0, -11.2, -66.5, -7.1),
    resolution=5_000.0,
)

# ---------------------------------------------------------------------------
# 4. Register BDC tile shapefiles as SpatialSources
#
# import_bdc_grids (corrected version) registers tiles ONLY as SpatialSource
# (spatial envelope with bbox). Simulation grids are already registered above.
# No overlap, no duplicate BR/5km registration.
# ---------------------------------------------------------------------------

print("\n=== 4. Registering BDC tile sources ===")
import_bdc_grids(
    cube,
    sm_path="zip://data/bdc_grids/BDC_SM_V2.zip",
    md_path="zip://data/bdc_grids/BDC_MD_V2.zip",
    lg_path="zip://data/bdc_grids/BDC_LG_V2.zip",
)

# ---------------------------------------------------------------------------
# 5. Register raw data sources
# ---------------------------------------------------------------------------

print("\n=== 5. Registering spatial sources ===")

cube.register_spatial_source(SpatialSource(
    id="maranhao_base",
    name="Ilha do Maranhão — raster EPSG:31983",
    format="raster",
    asset_url=BRMANGUE_DST,
    crs="EPSG:31983",
))
print("  [source] maranhao_base")

cube.register_spatial_source(SpatialSource(
    id="acre_base",
    name="Acre — vector EPSG:4326",
    format="vector",
    asset_url=ACRE_DST,
    crs="EPSG:4326",
))
print("  [source] acre_base")

def _check_path(url: str) -> str:
    """Strip protocol prefixes (zip://, file://) so os.path.exists() works."""
    for prefix in ("zip://", "file://"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return url


# Optional auxiliary sources — registered only if files are present.
# asset_url may use protocol prefixes (zip://) recognised by fiona/rasterio;
# _check_path strips them for the filesystem existence check.
_aux = [
    (
        "slope_brazil",
        "Brazil Slope 250 m",
        "data/raw/decliv_sc_250_poly_sirgas2000.tif",
        "raster",
        "EPSG:5880",
    ),
    (
        "terras_indigenas",
        "Terras Indígenas FUNAI 2010",
        "zip://data/raw/terras_indigenas_funai_2010_limpo_poly_sirgas2000.zip",
        "vector",
        "EPSG:5880",
    ),
    (
        "urban_centers",
        "Urban Centers (PNLT)",
        "data/raw/urban_center/centros_urbanos_m_100_pnlt_poly_sirgas2000.shp",
        "vector",
        "EPSG:5880",
    ),
    (
        "rios_pnlt",
        "Rivers PNLT",
        "data/raw/rios_pnlt/rios_pnlt_poly_sirgas2000.shp",
        "vector",
        "EPSG:5880",
    ),
]
for src_id, name, url, fmt, crs in _aux:
    if os.path.exists(_check_path(url)):
        cube.register_spatial_source(
            SpatialSource(id=src_id, name=name, format=fmt, asset_url=url, crs=crs)
        )
        print(f"  [source] {src_id}")
    else:
        print(f"  [warn]   {src_id} skipped — file not found: {_check_path(url)}")

# ---------------------------------------------------------------------------
# 6. Example derivation spec (declarative — not yet executed)
#
# Variable fields in this branch: name (str), operator (str),
# class_code (int | None).  No VarType / semantic_type.
# ---------------------------------------------------------------------------

print("\n=== 6. Example derivation spec ===")

acre_roads_derivation = SpatialDerivation(
    source_id="acre_base",
    grid_id="AC/5km",
    role="driver",
    variables=[
        Variable(name="dist_roads", operator="min_distance"),
    ],
)
print(f"  spec_hash: {acre_roads_derivation.spec_hash()}")
print(f"  to run:    cube.derive(acre_roads_derivation)")

print("\n=== Catalog ready ===")