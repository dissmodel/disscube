import sys
import os
from disscube.client import CubeClient
from disscube.models import GridSpec, DataSource, SpatialDerivation, Variable

# Fix Path: Add brmangue-dissmodel, dissmodel core, and disscube to path
# We use absolute paths based on the structure provided
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(base_dir, "brmangue-dissmodel"))
sys.path.insert(0, os.path.join(base_dir, "dissmodel"))
sys.path.insert(0, os.path.join(base_dir, "disscube"))

try:
    from brmangue.executor.brmangue_executor import BrmangueExecutor
    from dissmodel.executor import ExperimentRecord
except ImportError as e:
    print(f"Warning: Dependencies not found ({e}). Skipping execution part.")
    BrmangueExecutor = None
    ExperimentRecord = None

# Initialize client
# Note: catalog.json and data/ will be created/used in the current working directory
# When running from disscube root: python examples/example_03_brmangue.py
cube = CubeClient(catalog="catalog.json", store="./data/")

# 1. Register GridSpec
# Creating a 100m grid for the Brmangue area (São Luís)
grid_spec = GridSpec(
    id="BRMANGUE/100m",
    type="local",
    crs="EPSG:31983",
    resolution=100.0,
    bbox=[568900.0, 9692870.0, 609350.0, 9734650.0],
    description="Brmangue 100m Grid"
)
cube.register_grid(grid_spec)

# 2. Register DataSource
# Using the sample TIFF from brmangue-dissmodel
data_source = DataSource(
    id="fonte_brmangue",
    name="Brmangue Input Raster",
    format="raster",
    asset_url="../brmangue-dissmodel/examples/data/input/ilha_maranhao_epsg31983.tif",
    crs="EPSG:31983"
)
cube.register_source(data_source)

# 3. Declare SpatialDerivation
# We derive "uso", "alt", and "solo" from the same source for this example
# In a real scenario, these might come from different sources.
derivation = SpatialDerivation(
    source_id="fonte_brmangue",
    grid_id="BRMANGUE/100m",
    role="luc_observation",
    variables=[
        Variable(name="uso", operator="majority"),
        Variable(name="alt", operator="mean"),
        Variable(name="solo", operator="majority")
    ]
)

# 4. Execute pipeline (derive)
print("Executing derivation pipeline (this might take a few seconds)...")
cube.derive(derivation)

# 5. Load from Cube (DissCube now returns a standard RasterBackend)
variables = ["uso", "alt", "solo"]
print(f"Loading variables from cube: {variables}")
cube_backend = cube.to_lucc_data(variables)

print(f"Result type from Cube: {type(cube_backend)}")
print(f"Backend bands: {cube_backend.band_names()}")

if BrmangueExecutor and ExperimentRecord:
    print("\n--- Running BrmangueExecutor (Simulation) ---")
    
    # 6. Adapt Cube data for Brmangue (Responsibility of the Executor)
    executor_data = BrmangueExecutor.from_cube(cube_backend)
    
    # Setup a minimal ExperimentRecord
    record = ExperimentRecord(
        experiment_id="example_cube_integration",
        parameters={
            "end_time": 5,
            "interactive": False,
            "bands": ["uso"]
        },
        source={"uri": data_source.asset_url},
        input_format="tiff"
    )
    
    executor = BrmangueExecutor()
    # The executor.run() expects (backend, meta, start) and the record
    final_result = executor.run(executor_data, record)
    
    # 7. Save the results
    print("\nSaving simulation results...")
    executor.save(final_result, record)
        
    print(f"Simulation finished. Output saved to: {record.output_path}")
    for log in record.logs:
        print(f"LOG: {log}")
else:
    print("\nBrmangueExecutor not available or result failed. Integration test ends here.")
