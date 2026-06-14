"""
Zonal operators — window-based aggregates over raster and vector sources.

Each class registers itself automatically into ``OPERATOR_REGISTRY`` via
``Operator.__init_subclass__``.  No changes to the pipeline are required
when a new operator is added here.
"""

from __future__ import annotations

import numpy as np
import xarray as xr
import geopandas as gpd
import rasterio.features
from rasterio.warp import Resampling

from disscube.operators.base import Operator
from disscube.models.variable import Variable
from disscube.models.grid import GridSpec


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _rasterize(shapes: list, grid: GridSpec) -> np.ndarray:
    """Rasterize ``(geometry, value)`` pairs onto ``grid``, returning float32."""
    if not shapes:
        return np.zeros((grid.rows, grid.cols), dtype=np.float32)
    return rasterio.features.rasterize(
        shapes,
        out_shape=(grid.rows, grid.cols),
        transform=grid.transform,
        fill=0,
        all_touched=False,
    ).astype(np.float32)


def _wrap(arr: np.ndarray, grid: GridSpec) -> xr.DataArray:
    """Wrap a 2-D array as a grid-aligned DataArray."""
    return xr.DataArray(arr, dims=("y", "x"), coords={"y": grid.ys, "x": grid.xs})


def _passthrough(data: xr.DataArray) -> xr.DataArray:
    """Return the raster band as a plain (y, x) DataArray."""
    if "band" in data.dims:
        data = data.isel(band=0)
    return data.transpose("y", "x")


# ---------------------------------------------------------------------------
# Raster-only operators
# ---------------------------------------------------------------------------

class MeanOperator(Operator):
    name = "mean"
    _resampling = Resampling.average

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        raise TypeError(f"'mean' requires a raster source, got {type(data).__name__}")


class SumOperator(Operator):
    name = "sum"
    _resampling = Resampling.sum

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        raise TypeError(f"'sum' requires a raster source, got {type(data).__name__}")


class StdOperator(Operator):
    name = "std"
    # rasterio has no standard-deviation resampling; nearest is a placeholder.
    # True std requires a zonal-statistics pass (future work).
    _resampling = Resampling.nearest

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        raise TypeError(f"'std' requires a raster source, got {type(data).__name__}")


class MinOperator(Operator):
    name = "min"
    _resampling = Resampling.min

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        raise TypeError(f"'min' requires a raster source, got {type(data).__name__}")


class MaxOperator(Operator):
    name = "max"
    _resampling = Resampling.max

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        raise TypeError(f"'max' requires a raster source, got {type(data).__name__}")


# ---------------------------------------------------------------------------
# Raster + vector operators
# ---------------------------------------------------------------------------

class MajorityOperator(Operator):
    name = "majority"
    _resampling = Resampling.mode

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        if isinstance(data, gpd.GeoDataFrame):
            val = var.class_code if var.class_code is not None else 1
            shapes = [(g, val) for g in data.geometry if g is not None]
            return _wrap(_rasterize(shapes, grid), grid)
        raise TypeError(f"'majority' got unexpected type {type(data).__name__}")


class MinorityOperator(Operator):
    name = "minority"
    _resampling = Resampling.mode

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        if isinstance(data, gpd.GeoDataFrame):
            val = var.class_code if var.class_code is not None else 1
            shapes = [(g, val) for g in data.geometry if g is not None]
            return _wrap(_rasterize(shapes, grid), grid)
        raise TypeError(f"'minority' got unexpected type {type(data).__name__}")


class PercentageOperator(Operator):
    name = "percentage"
    requires_class_code = True
    _resampling = Resampling.mode

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        if isinstance(data, gpd.GeoDataFrame):
            shapes = [(g, var.class_code) for g in data.geometry if g is not None]
            return _wrap(_rasterize(shapes, grid), grid)
        raise TypeError(f"'percentage' got unexpected type {type(data).__name__}")


class AttributeOperator(Operator):
    """
    Rasterize a vector layer using a numeric column as the pixel value.

    The column name must match ``Variable.name`` (explicit contract:
    register the source with a column that matches the variable you intend
    to derive).
    """
    name = "attribute"
    _resampling = Resampling.nearest

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        if isinstance(data, gpd.GeoDataFrame):
            column = var.name
            if column in data.columns:
                valid = data[data.geometry.notnull() & data[column].notnull()]
                shapes = list(zip(valid.geometry, valid[column]))
            else:
                shapes = []
            return _wrap(_rasterize(shapes, grid), grid)
        raise TypeError(f"'attribute' got unexpected type {type(data).__name__}")


class PresenceOperator(Operator):
    """Binary mask: 1 where any feature is present, 0 elsewhere."""
    name = "presence"
    _resampling = Resampling.nearest

    def compute(self, data, var: Variable, grid: GridSpec) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            return _passthrough(data)
        if isinstance(data, gpd.GeoDataFrame):
            val = var.class_code if var.class_code is not None else 1
            shapes = [(g, val) for g in data.geometry if g is not None]
            return _wrap(_rasterize(shapes, grid), grid)
        raise TypeError(f"'presence' got unexpected type {type(data).__name__}")


# ---------------------------------------------------------------------------
# Legacy compatibility shim — kept so existing imports don't break
# ---------------------------------------------------------------------------

class ZonalAggregator:
    """
    Deprecated.  Use operator classes directly via ``OPERATOR_REGISTRY``.

    Kept as a thin compatibility shim; delegates to the appropriate
    ``Operator.compute()`` for each variable.
    """

    @staticmethod
    def aggregate(data, variables, grid_spec):
        import warnings
        warnings.warn(
            "ZonalAggregator is deprecated; use OPERATOR_REGISTRY operators directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        from disscube.operators.base import OPERATOR_REGISTRY
        ds = xr.Dataset(coords={"y": grid_spec.ys, "x": grid_spec.xs})
        for var in variables:
            op_cls = OPERATOR_REGISTRY.get(var.operator)
            if op_cls is None:
                raise ValueError(f"Unknown operator: {var.operator}")
            da = op_cls().compute(data, var, grid_spec)
            ds[var.name] = da
        return ds
