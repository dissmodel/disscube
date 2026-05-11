import numpy as np
import xarray as xr
import geopandas as gpd
import rasterio.features
from affine import Affine
from scipy.ndimage import distance_transform_edt

class ProximityAggregator:
    @staticmethod
    def aggregate(data: xr.DataArray | gpd.GeoDataFrame, variables, grid_spec):
        rows = grid_spec.rows
        cols = grid_spec.cols
        transform = grid_spec.transform
        xs = grid_spec.xs
        ys = grid_spec.ys
        var = variables[0]

        if isinstance(data, gpd.GeoDataFrame):
            if var.operator == "min_distance":
                # Rasterize to binary mask (1 where features exist)
                shapes = ((geom, 1) for geom in data.geometry if geom is not None)
                mask = rasterio.features.rasterize(
                    shapes,
                    out_shape=(rows, cols),
                    transform=transform,
                    fill=0,
                    all_touched=True
                )
                # Distance transform
                dist = distance_transform_edt(1 - mask) * grid_spec.resolution
                
                da = xr.DataArray(dist, dims=("y", "x"), coords={"y": ys, "x": xs})
                da.rio.write_crs(grid_spec.crs, inplace=True)
                da.rio.write_transform(transform, inplace=True)
                return da
            
            elif var.operator == "count":
                # For count, we can use rasterize with 'merge_alg=ADD' if available, 
                # but rasterio's rasterize doesn't support ADD directly like that.
                # Instead, we can use spatial join or iterate.
                # Faster way for many points: use numpy bincount with cell indices.
                
                # Filter valid geometries
                valid_data = data[data.geometry.notnull()]
                if valid_data.empty:
                    counts = np.zeros((rows, cols))
                else:
                    # Get pixel coordinates
                    # Note: grid_spec.transform is from north-up (origin at top-left)
                    # col = (x - minx) / res
                    # row = (maxy - y) / res
                    minx, miny, maxx, maxy = grid_spec.bbox
                    res = grid_spec.resolution
                    
                    # Get centroids of geometries
                    centroids = valid_data.geometry.centroid
                    
                    cols_idx = ((centroids.x - minx) / res).astype(int)
                    rows_idx = ((maxy - centroids.y) / res).astype(int)
                    
                    # Filter indices within bounds
                    mask = (cols_idx >= 0) & (cols_idx < cols) & (rows_idx >= 0) & (rows_idx < rows)
                    cols_idx = cols_idx[mask]
                    rows_idx = rows_idx[mask]
                    
                    # Flatten indices for bincount
                    flat_idx = rows_idx * cols + cols_idx
                    counts_flat = np.bincount(flat_idx, minlength=rows * cols)
                    counts = counts_flat.reshape((rows, cols))
                
                da = xr.DataArray(counts, dims=("y", "x"), coords={"y": ys, "x": xs})
                da.rio.write_crs(grid_spec.crs, inplace=True)
                da.rio.write_transform(transform, inplace=True)
                return da
            
        if isinstance(data, xr.DataArray):
            if "band" in data.dims:
                data = data.isel(band=0)
            return data.transpose("y", "x")

        return xr.DataArray(np.zeros((rows, cols)), dims=("y", "x"), coords={"y": ys, "x": xs})
