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

        if isinstance(data, gpd.GeoDataFrame):
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
            
            # If everything is 1 (mask covers everything), dist will be 0, which is fine.
            # If everything is 0 (no features), dist will be very large.
            # We can cap it or handle nodata if needed.
            
            da = xr.DataArray(dist, dims=("y", "x"), coords={"y": ys, "x": xs})
            da.rio.write_crs(grid_spec.crs, inplace=True)
            da.rio.write_transform(transform, inplace=True)
            return da
            
        if isinstance(data, xr.DataArray):
            if "band" in data.dims:
                data = data.isel(band=0)
            return data.transpose("y", "x")

        return xr.DataArray(np.zeros((rows, cols)), dims=("y", "x"), coords={"y": ys, "x": xs})
