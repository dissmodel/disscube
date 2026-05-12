from disscube.client import CubeClient
# Assume disslucc-continuous and dissmodel are in PYTHONPATH
try:
    from disslucc.infra.executors.clue_like_raster_executor import LUCCRasterExecutor
    from dissmodel.executor.schemas import ExperimentRecord
except ImportError:
    print("dissmodel or disslucc-continuous not found in path. Skipping execution part.")
    LUCCRasterExecutor = None

cube = CubeClient(catalog="catalog.db", store="./data/")

# Assuming variables are already derived
variables = ["forest_pct", "dist_roads", "dist_urban"]

# Integration point: to_lucc_data()
data = cube.to_lucc_data(variables, executor="lucc_raster")

print(f"Data type for LUCCRasterExecutor: {type(data)}")

if LUCCRasterExecutor:
    # Simulate platform execution
    # executor = LUCCRasterExecutor()
    # record = ExperimentRecord(...)
    # executor.run(data, record)
    print("Ready to run LUCCRasterExecutor.")
