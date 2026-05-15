"""
examples/04_lucc_pipeline.py

LUCC case study — land use change on Acre (AC/5km).

Derives land use class variables from the Acre vector source
and runs the LUCCRasterExecutor simulation.

Prerequisites
-------------
01_setup_catalog.py must have been run first:
  - catalog.db exists
  - AC/5km grid is registered (BDC Albers, 5 km pixels, snapped)
  - acre_base SpatialSource is registered

Run:
    python examples/04_lucc_pipeline.py
"""

from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable

try:
    from disslucc.infra.executors.clue_like_raster_executor import LUCCRasterExecutor
    from dissmodel.executor.schemas import ExperimentRecord
except ImportError as e:
    print(f"Warning: {e}. Skipping simulation step.")
    LUCCRasterExecutor = None
    ExperimentRecord  = None

GRID_ID   = "AC/5km"
SOURCE_ID = "acre_base"

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
# Derivation — land use class attributes f and d
# ---------------------------------------------------------------------------

derivation = SpatialDerivation(
    source_id=SOURCE_ID,
    grid_id=GRID_ID,
    role="luc_observation",
    variables=[
        Variable(name="f", operator="attribute"),
        Variable(name="d", operator="attribute"),
    ],
)

print(f"\n[derive] spec_hash: {derivation.spec_hash()}")
print("[derive] running pipeline …")
cube.derive(derivation)
print("[derive] done")

# ---------------------------------------------------------------------------
# Load derived variables
# ---------------------------------------------------------------------------

VARIABLES = ["f", "d"]
print(f"\n[load] {VARIABLES}")
backend = cube.to_lucc_data(VARIABLES)
print(f"[load] backend type: {type(backend)}")

# Quick sanity check on variable f
arr_f = backend.get("f")
valid = arr_f[arr_f > 0]
if valid.size:
    print(f"[check] f — mean (non-zero): {valid.mean():.4f}")

# ---------------------------------------------------------------------------
# Run LUCCRasterExecutor simulation (if available)
# ---------------------------------------------------------------------------

if LUCCRasterExecutor and ExperimentRecord:
    print("\n--- Running LUCCRasterExecutor ---")

    record = ExperimentRecord(
        experiment_id="lucc_acre_5km",
        parameters={
            "end_time": 10,
            "interactive": False,
        },
        source={"uri": source.asset_url},
        input_format="vector",
    )

    executor = LUCCRasterExecutor()
    result = executor.run(backend, record)
    executor.save(result, record)

    print(f"Simulation done. Output: {record.output_path}")
    for log in record.logs:
        print(f"  LOG: {log}")
else:
    print("\nLUCCRasterExecutor not available — derivation step complete.")
