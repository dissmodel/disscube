"""
examples/case_studies/lucc_acre/03_temporal_drivers.py

Demonstrates how to load and use temporal variables (dist_cidades) 
in a LUCC simulation loop.

Usage:
    python examples/case_studies/lucc_acre/03_temporal_drivers.py
"""

from disscube.client import CubeClient

cube = CubeClient(catalog="catalog.db", store="./data/")

print("=== Loading temporal LUCC data ===")

# Load variables for the full period to get all temporal slices
backend = cube.to_lucc_data(
    ["slope", "dist_cidades"],
    grid_id="BR/5km",
    period=("2000", "2025"),
)

print(f"Backend loaded with: {backend.band_names()}")
if backend.is_temporal:
    print(f"Time steps: {backend.time_coords}")

# Simulation Loop Simulation
print("\n=== Simulation Loop Simulation ===")
years = ["2000", "2005", "2010", "2015", "2020"]
for year in years:
    # backend.get() automatically finds the valid slice for the given year
    d_urb = backend.get("dist_cidades", time=year)
    print(f"Year {year}: dist_cidades slice retrieved (shape: {d_urb.shape})")
