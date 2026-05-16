"""
examples/lucc_pipeline_temporal.py

Demonstrates how to load and use temporal variables in a LUCC pipeline.
This script assumes that 02_register_drivers.py has been run, creating:
  - slope (static)
  - dist_cidades (temporal, with slices for 2000 and 2015)

Usage:
    python examples/lucc_pipeline_temporal.py
"""

from disscube.client import CubeClient

# 1. Initialize CubeClient
# Point to the same catalog and data store used in registration
cube = CubeClient(catalog="catalog.db", store="./data/")

print("=== Loading temporal LUCC data ===")

# 2. Load variables for a specific period
# to_lucc_data returns a RasterBackend which efficiently manages 
# both static and temporal layers.
#
# Period ("2000", "2025") ensures we get both slices of dist_cidades
# if they were registered with those temporal markers.
backend = cube.to_lucc_data(
    ["slope", "dist_cidades"],
    grid_id="BR/5km",
    period=("2000", "2025"),
)

print(f"Backend loaded with variables: {backend.band_names}")
if backend.is_temporal:
    print(f"Available time steps: {backend.time_coords}")

# 3. Accessing data in the model loop
# Static variables don't need a time argument
slope = backend.get("slope")
print(f"\n[static]  slope shape: {slope.shape}")

# Temporal variables can be queried by year
# The backend finds the slice that matches or is valid for that year
try:
    dist_2005 = backend.get("dist_cidades", time="2000")
    print(f"[temporal] dist_cidades (year 2000) shape: {dist_2005.shape}")
    
    dist_2020 = backend.get("dist_cidades", time="2015")
    print(f"[temporal] dist_cidades (year 2015) shape: {dist_2020.shape}")
except Exception as e:
    print(f"\n[error] Could not retrieve temporal slice: {e}")
    print("Hint: Ensure VariableWriter is updated to populate DerivedVariable.times from SpatialDerivation.valid_from")

# 4. Example of how this looks in a typical CA model loop
print("\n=== Simulation Loop Simulation ===")
years = ["2000", "2005", "2010", "2015", "2020"]
for year in years:
    # In a real model, 'year' would be the current simulation step
    # get() handles the temporal lookup automatically
    d_urb = backend.get("dist_cidades", time=year)
    print(f"Year {year}: dist_cidades slice retrieved.")
