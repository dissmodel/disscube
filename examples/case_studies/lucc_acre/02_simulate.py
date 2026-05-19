"""
examples/case_studies/lucc_acre/02_simulate.py

LUCC case study — Executes the LUCCRasterExecutor simulation using derived variables.

Usage:
    python examples/case_studies/lucc_acre/02_simulate.py
"""

from disscube.client import CubeClient

try:
    from disslucc.infra.executors.clue_like_raster_executor import LUCCRasterExecutor
    from dissmodel.executor.schemas import ExperimentRecord
except ImportError as e:
    print(f"Warning: {e}. Skipping simulation step.")
    LUCCRasterExecutor = None
    ExperimentRecord  = None

GRID_ID   = "AC/5km"
SOURCE_ID = "acre_base"
VARIABLES = ["f", "d"]

cube = CubeClient(catalog="catalog.db", store="./data/")

# 1. Load derived variables
print(f"\n[load] {VARIABLES} @ {GRID_ID}")
backend = cube.to_lucc_data(VARIABLES, grid_id=GRID_ID)
print(f"  backend type: {type(backend)}")

# 2. Run simulation
if LUCCRasterExecutor and ExperimentRecord:
    print("\n--- Running LUCCRasterExecutor ---")
    source = cube.catalog.get_spatial_source(SOURCE_ID)

    record = ExperimentRecord(
        experiment_id="lucc_acre_5km",
        parameters={"end_time": 10, "interactive": False},
        source={"uri": source.asset_url if source else "unknown"},
        input_format="vector",
    )

    executor = LUCCRasterExecutor()
    result = executor.run(backend, record)
    executor.save(result, record)

    print(f"Simulation done. Output: {record.output_path}")
else:
    print("\nLUCCRasterExecutor not available — simulation skipped.")
