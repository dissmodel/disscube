from typing import Optional, List, Any
import os
import xarray as xr
from dissmodel.geo.raster.backend import RasterBackend
from disscube.catalog import JsonCatalogStore
from disscube.storage import AssetStore
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, DerivedVariable, SpatialRelation
from disscube.pipeline import PipelineContext
from disscube.pipeline.normalizer import Normalizer
from disscube.pipeline.aligner import GridAligner
from disscube.pipeline.aggregator import Aggregator
from disscube.pipeline.writer import VariableWriter

class CubeClient:
    def __init__(self, catalog: str, store: str):
        self.catalog = JsonCatalogStore(catalog)
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

    def derive(self, derivation: SpatialDerivation) -> List[DerivedVariable]:
        # Enriquecer derivação com relações diretas se não estiverem presentes
        # Trabalhamos em uma cópia para não alterar o objeto original do usuário
        derivation = derivation.model_copy(deep=True)
        if not derivation.relations:
            derivation.relations = self.get_relations(derivation.grid_id)

        spec_hash = derivation.spec_hash()
        
        # Try to identify tile_id from source_id
        tile_id = None
        if derivation.grid_id.startswith("BDC_"):
            parts = derivation.source_id.split("_")
            if len(parts) >= 3:
                tile_id = parts[-1]

        # Check cache and physical existence for ALL expected variables
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

        ctx = PipelineContext(source=source, grid=grid, derivation=derivation)
        
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

    def load(self, variable_id: str, tile_id: Optional[str] = None) -> xr.DataArray:
        # Search for derived variable
        # For simplicity, assuming variable_id is name or ID
        matches = []
        for d in self.catalog.search_derived_variables(tile_id=tile_id):
            if d.id == variable_id or d.name == variable_id:
                matches.append(d)
        
        if not matches:
            raise ValueError(f"Derived variable not found: {variable_id}")
            
        if len(matches) > 1 and tile_id is None:
            tile_ids = [m.tile_id for m in matches if m.tile_id]
            raise ValueError(f"Multiple tiles found for {variable_id}: {tile_ids}. Please specify tile_id.")
            
        derived = matches[0]
        return xr.open_zarr(derived.asset_url)[derived.name]

    def to_lucc_data(self, variables: List[str], **kwargs) -> RasterBackend:
        """
        Standard integration point for the DisSModel ecosystem.
        Returns a RasterBackend containing all requested variables as bands.
        """
        # Load all variables into a single Dataset
        ds_list = [self.load(v) for v in variables]
        
        # Extract CRS from the first variable before they are merged
        detected_crs = ds_list[0].attrs.get("crs")
        if not detected_crs and "spatial_ref" in ds_list[0].coords:
            try:
                detected_crs = ds_list[0].rio.crs
            except:
                pass

        # Merge
        ds = xr.merge(ds_list, compat="override")
        
        # Build RasterBackend
        backend = RasterBackend.from_xarray(ds)
        
        # Force CRS injection if we detected it
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
