from typing import Optional, List, Any
import os
import numpy as np
import xarray as xr
from dissmodel.geo.raster.backend import RasterBackend
from disscube.catalog.sqlite_store import SqliteCatalogStore
from disscube.storage import AssetStore
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, DerivedVariable, SpatialRelation
from disscube.pipeline import PipelineContext
from disscube.pipeline.normalizer import Normalizer
from disscube.pipeline.aligner import GridAligner
from disscube.pipeline.aggregator import Aggregator
from disscube.pipeline.writer import VariableWriter


class CubeClient:
    def __init__(self, catalog: str, store: str):
        self.catalog = SqliteCatalogStore(catalog)
        self.store = AssetStore(store)

    def register_grid(self, grid: GridSpec):
        self.catalog.save_grid(grid)

    def register_spatial_source(self, source: SpatialSource):
        self.catalog.save_spatial_source(source)

    def register_relation(self, relation: SpatialRelation):
        self.catalog.save_relation(relation)

    def get_relations(self, grid_id: str) -> List[SpatialRelation]:
        return self.catalog.get_relations(grid_id)

    def search(self, grid: Optional[str] = None, role: Optional[str] = None) -> List[DerivedVariable]:
        return self.catalog.search_derived_variables(grid_id=grid, role=role)

    def derive(self, derivation: SpatialDerivation, tile_id: Optional[str] = None) -> List[DerivedVariable]:
        derivation = derivation.model_copy(deep=True)
        if not derivation.relations:
            derivation.relations = self.get_relations(derivation.grid_id)

        spec_hash = derivation.spec_hash()

        expected = {v.name for v in derivation.variables}
        all_derived = self.catalog.search_derived_variables(tile_id=tile_id)
        cached_vars = [
            d for d in all_derived
            if d.spec_hash == spec_hash and self.store.fs.exists(d.asset_url)
        ]
        cached_names = {d.name for d in cached_vars}

        if expected == cached_names:
            return cached_vars

        source = self.catalog.get_spatial_source(derivation.source_id)
        if not source:
            raise ValueError(f"SpatialSource not found: {derivation.source_id}")

        grid = self.catalog.get_grid(derivation.grid_id)
        if not grid:
            raise ValueError(f"Grid not found: {derivation.grid_id}")

        if tile_id:
            tile_source = self.catalog.get_spatial_source(f"{grid.id}_{tile_id}")
            if not tile_source or not tile_source.bbox:
                raise ValueError(f"Tile {tile_id} with valid bbox not found for grid {grid.id}")

            grid = GridSpec(
                id=grid.id,
                type=grid.type,
                crs=grid.crs,
                resolution=grid.resolution,
                bbox=tile_source.bbox,
                description=f"Temporary tile grid for {tile_id}"
            )

        ctx = PipelineContext(source=source, grid=grid, derivation=derivation, tile_id=tile_id)

        pipeline = [
            Normalizer(),
            GridAligner(),
            Aggregator(),
            VariableWriter(self.store, self.catalog)
        ]

        for stage in pipeline:
            ctx = stage.execute(ctx)

        return [
            d for d in self.catalog.search_derived_variables(tile_id=tile_id)
            if d.spec_hash == spec_hash
        ]

    def load(
        self,
        variable_id: str,
        tile_id: Optional[str] = None,
        grid_id: Optional[str] = None,
    ) -> xr.DataArray:
        """
        Load a derived variable as an xr.DataArray.

        For temporal variables (DerivedVariable.times is non-empty), returns
        a DataArray with dims (time, y, x). For static variables, returns (y, x).
        """
        matches = []
        for d in self.catalog.search_derived_variables(tile_id=tile_id, grid_id=grid_id):
            if d.id == variable_id or d.name == variable_id:
                matches.append(d)

        if not matches:
            msg = f"Derived variable not found: {variable_id}"
            if grid_id:
                msg += f" on grid {grid_id}"
            raise ValueError(msg)

        if len(matches) > 1 and tile_id is None and not grid_id:
            grid_ids = list(set(m.grid_id for m in matches))
            if len(grid_ids) > 1:
                raise ValueError(
                    f"Multiple grids found for {variable_id}: {grid_ids}. "
                    "Please specify grid_id."
                )

        # Separate temporal from static matches
        temporal = [d for d in matches if d.times]
        static   = [d for d in matches if not d.times]

        if temporal:
            # Stack temporal slices along time axis sorted by first time value
            temporal_sorted = sorted(temporal, key=lambda d: d.times[0])
            slices = []
            time_coords = []
            for d in temporal_sorted:
                da = xr.open_zarr(d.asset_url)[d.name]
                slices.append(da)
                time_coords.extend(d.times)
            if len(slices) == 1:
                return slices[0]
            return xr.concat(slices, dim=xr.DataArray(time_coords, dims="time"))

        # Static — original behaviour
        derived = static[0]
        return xr.open_zarr(derived.asset_url)[derived.name]

    def to_lucc_data(
        self,
        variables: List[str],
        grid_id: Optional[str] = None,
        period: Optional[tuple[str, str]] = None,
    ) -> RasterBackend:
        """
        Standard integration point for the DisSModel ecosystem.
        Returns a RasterBackend containing all requested variables.

        Static variables are stored as (y, x) arrays — identical to the
        previous behaviour; existing executors require no changes.

        Temporal variables are stored as (time, y, x) arrays with an
        explicit time axis in ``backend.time_coords``. CA models retrieve
        a 2D slice via ``backend.get(name, time=step)``.

        Parameters
        ----------
        variables : list[str]
            Names of derived variables to load.
        grid_id : str | None
            Restrict search to a specific grid. Required when the same
            variable name exists on multiple grids.
        period : tuple[str, str] | None
            Optional ``(start, end)`` filter for temporal variables.
            Only time slices whose value falls within [start, end] are loaded.
            Static variables are unaffected.
            Example: ``period=("2000", "2014")``
        """
        # Detect CRS from first successfully loaded variable
        detected_crs = None
        backend = None

        for var_name in variables:
            da = self.load(var_name, grid_id=grid_id)

            # CRS detection — run once
            if detected_crs is None:
                detected_crs = da.attrs.get("crs")
                if not detected_crs and "spatial_ref" in da.coords:
                    try:
                        detected_crs = da.rio.crs
                    except Exception:
                        pass

            # Initialise backend from first variable
            if backend is None:
                if da.ndim == 2:
                    rows, cols = da.sizes["y"], da.sizes["x"]
                else:
                    rows, cols = da.sizes["y"], da.sizes["x"]
                backend = RasterBackend(shape=(rows, cols))

            if da.ndim == 3 and "time" in da.dims:
                # Temporal variable ─ optionally filter by period
                if period is not None:
                    start, end = period
                    # Ensure comparison is done with consistent types (e.g. all ints if coordinates are ints)
                    time_vals = da.coords["time"].values
                    if len(time_vals) > 0 and isinstance(time_vals[0], (int, np.integer)):
                        try:
                            start_val, end_val = int(start), int(end)
                        except ValueError:
                            start_val, end_val = start, end
                    else:
                        start_val, end_val = start, end

                    mask = (time_vals >= start_val) & (time_vals <= end_val)
                    da = da.isel(time=mask)

                if da.sizes.get("time", 0) == 0:
                    # No slices in requested period — skip with warning
                    print(f"  [warn] {var_name}: no data in period {period}, skipped")
                    continue

                time_coords = da.coords["time"].values
                arr = da.transpose("time", "y", "x").values
                backend.set(var_name, arr, time=time_coords)

            else:
                # Static variable — backward-compatible path
                arr = da.transpose("y", "x").values
                backend.set(var_name, arr)

        if backend is None:
            raise ValueError(f"No variables could be loaded: {variables}")

        if backend.crs is None and detected_crs:
            backend.crs = detected_crs

        return backend

    def to_data_source(self, derived_id: str) -> dict:
        """
        Helper for dissmodel-platform ExperimentRecord.
        """
        derived = None
        for d in self.catalog.search_derived_variables():
            if d.id == derived_id:
                derived = d
                break

        if not derived:
            raise ValueError(f"Derived variable not found: {derived_id}")

        return {
            "uri": derived.asset_url,
            "checksum": derived.content_hash,
            "type": "local" if derived.asset_url.startswith("/") else "s3"
        }
