"""
GridAligner — reprojects source data to the target GridSpec.

For raster sources each variable is aligned independently using the
resampling method declared by its Operator class, so ``majority`` uses
``Resampling.mode`` while ``mean`` uses ``Resampling.average`` — even when
both are derived from the same multi-band file.

The output is an ``xr.Dataset`` keyed by variable name; the Aggregator
picks each DataArray and delegates to the operator's ``compute()`` method.

For vector sources the GeoDataFrame is reprojected and clipped to the grid
bounding box; the Aggregator then calls each operator's ``compute()`` to
rasterize.

Invariant enforced at the end of raster alignment:
    aligned.rio.shape == (grid.rows, grid.cols)

A mismatch raises ``ValueError`` immediately so misalignments surface as
loud errors rather than silent downstream corruption.
"""

from __future__ import annotations

import logging

import rioxarray  # noqa: F401 — registers the .rio accessor
import xarray as xr
import geopandas as gpd
from pyproj import CRS as ProjCRS
from rasterio.warp import Resampling
from shapely.geometry import box

from disscube.operators.base import OPERATOR_REGISTRY
from disscube.pipeline import PipelineStage, PipelineContext
from disscube.models.grid import GridSpec
from disscube.models.variable import Variable

log = logging.getLogger(__name__)


class GridAligner(PipelineStage):
    def execute(self, ctx: PipelineContext) -> PipelineContext:
        grid = ctx.grid
        fmt = ctx.source.format

        if fmt == "raster":
            ctx.data = self._align_raster(
                ctx.source.asset_url,
                grid,
                ctx.derivation.variables,
                ctx.source.band_map,
            )
        elif fmt == "vector":
            gdf: gpd.GeoDataFrame = ctx.data
            try:
                needs_reproject = not ProjCRS.from_user_input(gdf.crs).equals(
                    ProjCRS.from_user_input(grid.crs)
                )
            except Exception:
                needs_reproject = str(gdf.crs) != str(grid.crs)
            if needs_reproject:
                gdf = gdf.to_crs(grid.crs)
            gdf = gdf.clip(box(*grid.bbox))
            ctx.data = gdf

        return ctx

    # ------------------------------------------------------------------
    # Raster alignment — one aligned DataArray per derived variable
    # ------------------------------------------------------------------

    def _align_raster(
        self,
        url: str,
        grid: GridSpec,
        variables: list[Variable],
        band_map: dict[str, int],
    ) -> xr.Dataset:
        """
        Reproject and resample the source raster for each variable.

        Returns an ``xr.Dataset`` with one data variable per ``Variable``,
        each resampled with the method appropriate for its operator
        (e.g. ``Resampling.mode`` for ``majority``,
        ``Resampling.average`` for ``mean``).

        Parameters
        ----------
        url : str
            Path or URL to the source raster.
        grid : GridSpec
            Target spatial grid.
        variables : list[Variable]
            Variables to derive; determines band selection and resampling.
        band_map : dict[str, int]
            Optional ``{variable_name: 1-based band index}`` from the source.
        """
        ds_src = rioxarray.open_rasterio(url)
        result = xr.Dataset(coords={"y": grid.ys, "x": grid.xs})

        for i, var in enumerate(variables):
            # ── Band selection ─────────────────────────────────────────
            if "band" in ds_src.dims and ds_src.sizes["band"] > 1:
                if band_map and var.name in band_map:
                    band_idx = band_map[var.name] - 1  # 1-based → 0-based
                    if not (0 <= band_idx < ds_src.sizes["band"]):
                        raise ValueError(
                            f"Band index {band_idx + 1} for variable "
                            f"'{var.name}' is out of range; "
                            f"source has {ds_src.sizes['band']} bands."
                        )
                elif i < ds_src.sizes["band"]:
                    band_idx = i
                else:
                    raise ValueError(
                        f"No band available for variable '{var.name}' at "
                        f"index {i}; source has {ds_src.sizes['band']} bands "
                        "and no band_map was provided."
                    )
                band = ds_src.isel(band=band_idx)
            else:
                band = ds_src.isel(band=0) if "band" in ds_src.dims else ds_src

            # ── Per-operator resampling method ─────────────────────────
            op_cls = OPERATOR_REGISTRY.get(var.operator)
            resampling: Resampling = (
                op_cls.resampling() if op_cls else Resampling.nearest
            )

            # ── Reproject to target grid ───────────────────────────────
            aligned = band.rio.reproject(
                grid.crs,
                shape=(grid.rows, grid.cols),
                transform=grid.transform,
                resampling=resampling,
            )

            # ── Alignment invariant ────────────────────────────────────
            actual = aligned.rio.shape
            expected = (grid.rows, grid.cols)
            if actual != expected:
                raise ValueError(
                    f"GridAligner: variable '{var.name}' alignment produced "
                    f"shape {actual}, expected {expected} for grid '{grid.id}'. "
                    f"Source: {url}"
                )

            result[var.name] = aligned.transpose("y", "x")
            log.debug(
                "aligned '%s' via '%s' (resampling=%s, shape=%s)",
                var.name, var.operator, resampling.name, actual,
            )

        return result
