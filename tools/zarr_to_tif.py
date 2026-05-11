from disscube.client import CubeClient
import xarray as xr
import rioxarray
import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Export a derived Zarr variable to GeoTIFF.")
    parser.add_argument("grid_id", help="The ID of the grid (e.g., BR/5km)")
    parser.add_argument("variable", help="The name of the variable (e.g., mean_slope)")
    parser.add_argument("--output", "-o", help="Output TIFF path (optional)")
    
    args = parser.parse_args()

    # Initialize client
    cube = CubeClient(catalog="catalog.json", store="./data/")

    # Search for the specific variable
    grid = cube.catalog.get_grid(args.grid_id)
    if not grid:
        print(f"Error: Grid '{args.grid_id}' not found in catalog.")
        sys.exit(1)

    derived = cube.search(grid=args.grid_id, role="driver")
    target_var = next((d for d in derived if d.name == args.variable), None)

    if not target_var:
        print(f"Error: Variable '{args.variable}' for grid '{args.grid_id}' not found in catalog.")
        sys.exit(1)

    zarr_path = target_var.asset_url
    output_tif = args.output or f"outputs/export_{args.grid_id.replace('/', '_')}_{args.variable}.tif"

    os.makedirs(os.path.dirname(output_tif), exist_ok=True)

    print(f"Opening Zarr: {zarr_path}")
    ds = xr.open_zarr(zarr_path)
    da = ds[args.variable]

    # Write CRS from catalog grid definition
    da.rio.write_crs(grid.crs, inplace=True)

    print(f"Exporting to TIF: {output_tif}")
    da.rio.to_raster(output_tif)
    print(f"Done. File saved at: {output_tif}")

if __name__ == "__main__":
    main()
