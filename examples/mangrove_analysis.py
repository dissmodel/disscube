"""
examples/03_mangrove_analysis.py

BR-MANGUE case study — coastal dynamics on Ilha do Maranhão.

Derives land use variables from the Maranhão raster and runs
the BrmangueExecutor simulation.

Prerequisites
-------------
01_setup_catalog.py must have been run first:
  - catalog.db exists
  - MA/100m grid is registered (EPSG:31983, 100 m pixels)
  - maranhao_base SpatialSource is registered

Run:
    python examples/03_mangrove_analysis.py
"""

from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable

try:
    from brmangue.executor.brmangue_executor import BrmangueExecutor
    from dissmodel.executor import ExperimentRecord
except ImportError as e:
    print(f"Warning: {e}. Skipping simulation step.")
    BrmangueExecutor = None
    ExperimentRecord = None

GRID_ID   = "MA/100m"
SOURCE_ID = "maranhao_base"

# ---------------------------------------------------------------------------
# Initialize client
# ---------------------------------------------------------------------------

cube = CubeClient(catalog="catalog.db", store="./data/")

# Sanity checks — both must exist from 01_setup_catalog.py
grid = cube.catalog.get_grid(GRID_ID)
if grid is None:
    raise RuntimeError(f"Grid {GRID_ID!r} not found. Run 01_setup_catalog.py first.")
print(f"[ok] grid {GRID_ID}  {grid.rows} rows × {grid.cols} cols")

source = cube.catalog.get_spatial_source(SOURCE_ID)
if source is None:
    raise RuntimeError(f"Source {SOURCE_ID!r} not found. Run 01_setup_catalog.py first.")
print(f"[ok] source {SOURCE_ID}  →  {source.asset_url}")

# ---------------------------------------------------------------------------
# Derivation — uso, alt, solo from maranhao_base raster
# ---------------------------------------------------------------------------

derivation = SpatialDerivation(
    source_id=SOURCE_ID,
    grid_id=GRID_ID,
    role="luc_observation",
    variables=[
        Variable(name="uso",  operator="majority"),
        Variable(name="alt",  operator="mean"),
        Variable(name="solo", operator="majority"),
    ],
)

print(f"\n[derive] spec_hash: {derivation.spec_hash()}")
print("[derive] running pipeline …")
cube.derive(derivation)
print("[derive] done")

# ---------------------------------------------------------------------------
# Load derived variables
# ---------------------------------------------------------------------------

VARIABLES = ["uso", "alt", "solo"]
print(f"\n[load] {VARIABLES}")
backend = cube.to_lucc_data(VARIABLES)
print(f"[load] backend type: {type(backend)}")
print(f"[load] bands: {backend.band_names()}")

# ---------------------------------------------------------------------------
# Run BrmangueExecutor simulation (if available)
# ---------------------------------------------------------------------------

if BrmangueExecutor and ExperimentRecord:
    print("\n--- Running BrmangueExecutor ---")

    record = ExperimentRecord(
        experiment_id="brmangue_cube_integration",
        parameters={
            "end_time": 5,
            "interactive": False,
            "bands": ["uso"],
        },
        source={"uri": source.asset_url},
        input_format="tiff",
    )

    executor = BrmangueExecutor()
    executor_data = BrmangueExecutor.from_cube(backend)
    result = executor.run(executor_data, record)
    executor.save(result, record)

    print(f"Simulation done. Output: {record.output_path}")
    for log in record.logs:
        print(f"  LOG: {log}")
else:
    print("\nBrmangueExecutor not available — derivation step complete.")
