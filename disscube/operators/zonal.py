import numpy as np
import xarray as xr
import rioxarray
import geopandas as gpd
import rasterio.features
from affine import Affine

class ZonalAggregator:
    @staticmethod
    def aggregate(data: xr.DataArray | gpd.GeoDataFrame, variables, grid_spec):
        rows = int((grid_spec.bbox[3] - grid_spec.bbox[1]) / grid_spec.resolution)
        cols = int((grid_spec.bbox[2] - grid_spec.bbox[0]) / grid_spec.resolution)
        
        # North-up transform: origin at (minx, maxy), negative y-scale
        transform = Affine.translation(grid_spec.bbox[0], grid_spec.bbox[3]) * Affine.scale(grid_spec.resolution, -grid_spec.resolution)
        
        # Calculate cell centers for xarray coordinates (decreasing Y for North-up)
        xs = np.arange(cols) * grid_spec.resolution + grid_spec.bbox[0] + grid_spec.resolution/2
        ys = grid_spec.bbox[3] - (np.arange(rows) * grid_spec.resolution + grid_spec.resolution/2)

        if isinstance(data, gpd.GeoDataFrame):
            # Use the attribute if requested, otherwise use class_code
            column = variables[0].name if variables[0].operator == "attribute" else None
            
            if column and column in data.columns:
                # Filter out None geometries and get values
                valid_mask = data.geometry.notnull()
                shapes = zip(data.geometry[valid_mask], data[column][valid_mask])
            else:
                val = variables[0].class_code if variables[0].class_code is not None else 1
                shapes = ((geom, val) for geom in data.geometry if geom is not None)
            
            raster = rasterio.features.rasterize(
                shapes,
                out_shape=(rows, cols),
                transform=transform,
                fill=0,
                all_touched=True
            )
            
            da = xr.DataArray(raster, dims=("y", "x"), coords={"y": ys, "x": xs})
            da.rio.write_crs(grid_spec.crs, inplace=True)
            da.rio.write_transform(transform, inplace=True)
            return da
        
        if isinstance(data, xr.DataArray):
            # TODO: Para raster já alinhado pelo GridAligner, o operador é aplicado
            # implicitamente pelo resampling (Nearest para categórico, Bilinear para contínuo).
            # Implementar agregação explícita quando source_resolution != grid_resolution.
            if "band" in data.dims:
                data = data.isel(band=0)
            return data.transpose("y", "x")
        
        return xr.DataArray(np.zeros((rows, cols)), dims=("y", "x"), coords={"y": ys, "x": xs})
