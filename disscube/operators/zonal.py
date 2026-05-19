import numpy as np
import xarray as xr
import rioxarray
import geopandas as gpd
import rasterio.features
from affine import Affine

class ZonalAggregator:
    @staticmethod
    def aggregate(data: xr.DataArray | gpd.GeoDataFrame, variables, grid_spec):
        rows = grid_spec.rows
        cols = grid_spec.cols
        transform = grid_spec.transform
        xs = grid_spec.xs
        ys = grid_spec.ys

        if isinstance(data, gpd.GeoDataFrame):
            ds = xr.Dataset(coords={"y": ys, "x": xs})
            ds.rio.write_crs(grid_spec.crs, inplace=True)
            ds.rio.write_transform(transform, inplace=True)

            for var in variables:
                op = var.operator
                column = var.name if op == "attribute" else None
                
                if op == "presence":
                    val = var.class_code if var.class_code is not None else 1
                    shapes = [(geom, val) for geom in data.geometry if geom is not None]
                elif column and column in data.columns:
                    valid_mask = (data.geometry.notnull()) & (data[column].notnull())
                    shapes = list(zip(data.geometry[valid_mask], data[column][valid_mask]))
                else:
                    val = var.class_code if var.class_code is not None else 1
                    shapes = [(geom, val) for geom in data.geometry if geom is not None]
                
                if not shapes:
                    raster = np.zeros((rows, cols), dtype=np.float32)
                else:
                    raster = rasterio.features.rasterize(
                        shapes,
                        out_shape=(rows, cols),
                        transform=transform,
                        fill=0,
                        all_touched=False
                    )
                
                ds[var.name] = (("y", "x"), raster)
            
            return ds
        
        if isinstance(data, xr.DataArray):
            if "band" in data.dims:
                data = data.isel(band=0)
            
            # Use the variable name if provided, or preserve current name
            name = variables[0].name if variables else data.name
            if not name:
                name = "variable"
            
            # Convert single DataArray to Dataset for uniform writer handling
            return data.transpose("y", "x").to_dataset(name=name)
        
        return xr.Dataset(coords={"y": ys, "x": xs})
