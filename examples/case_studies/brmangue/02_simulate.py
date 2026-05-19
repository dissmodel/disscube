"""
examples/case_studies/brmangue/02_simulate.py

BR-MANGUE case study — Executes the BrmangueExecutor simulation using derived variables.

Usage:
    python examples/case_studies/brmangue/02_simulate.py
"""

from disscube.client import CubeClient

try:
    from brmangue.executor.brmangue_executor import BrmangueExecutor
    from dissmodel.executor import ExperimentRecord
except ImportError as e:
    print(f"Warning: {e}. Skipping simulation step.")
    BrmangueExecutor = None
    ExperimentRecord = None

GRID_ID   = "ilha_maranhao/100m"
SOURCE_ID = "maranhao_base"
VARIABLES = ["uso", "alt", "solo"]

cube = CubeClient(catalog="catalog.db", store="./data/")

# 1. Load derived variables
print(f"\n[load] {VARIABLES} @ {GRID_ID}")
backend = cube.to_lucc_data(VARIABLES, grid_id=GRID_ID)
print(f"  bands: {backend.band_names()}")

# 2. Run simulation
if BrmangueExecutor and ExperimentRecord:
    print("\n--- Running BrmangueExecutor ---")
    source = cube.catalog.get_spatial_source(SOURCE_ID)
    
    record = ExperimentRecord(
        experiment_id="brmangue_cube_integration",
        parameters={"end_time": 5, "interactive": False, "bands": ["uso"]},
        source={"uri": source.asset_url if source else "unknown"},
        input_format="tiff",
    )

    executor = BrmangueExecutor()
    executor_data = BrmangueExecutor.from_cube(backend)
    result = executor.run(executor_data, record)
    executor.save(result, record)

    print(f"Simulation done. Output: {record.output_path}")
else:
    print("\nBrmangueExecutor not available — simulation skipped.")
