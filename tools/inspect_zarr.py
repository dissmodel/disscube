import xarray as xr
import sys

zarr_path = "./data/derived/76537e3a02def3416d9d2ca73bcda799be39da4b17b595870940181c7eb91f50/dist_sedes.zarr"
print(f"Inspecting Zarr: {zarr_path}")
try:
    ds = xr.open_zarr(zarr_path)
    print("Dataset:")
    print(ds)
    print("\nCoordinates:")
    for coord in ds.coords:
        print(f"  {coord}: {ds[coord].values[:5]} ... (shape: {ds[coord].shape})")
    print("\nAttributes:")
    print(ds.attrs)
    if "dist_sedes" in ds:
        print("\nVariable 'dist_sedes' attributes:")
        print(ds.dist_sedes.attrs)
except Exception as e:
    print(f"Error: {e}")
