import zarr
import xarray as xr
from pathlib import Path
from disscube.pipeline import PipelineStage, PipelineContext
from disscube.models import DerivedVariable

class VariableWriter(PipelineStage):
    def __init__(self, storage, catalog):
        self.storage = storage
        self.catalog = catalog

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        ds = ctx.data
        grid = ctx.grid
        derivation = ctx.derivation
        spec_hash = derivation.spec_hash()
        
        # Save each variable to Zarr
        for var_name in ds.data_vars:
            da = ds[var_name]
            
            # Ensure spatial_ref coordinate is included if it exists in the dataset
            if "spatial_ref" in ds.coords and "spatial_ref" not in da.coords:
                da = da.assign_coords({"spatial_ref": ds.coords["spatial_ref"]})
            
            # Add metadata
            da.attrs["grid_id"] = grid.id
            da.attrs["role"] = derivation.role
            da.attrs["spec_hash"] = spec_hash
            if "spatial_ref" in da.coords:
                da.attrs["crs"] = grid.crs
            
            relative_path = f"derived/{spec_hash}/{var_name}.zarr"
            full_path = self.storage.get_full_path(relative_path)
            
            # Save as dataset to preserve all coordinates (including spatial_ref)
            da.to_dataset(name=var_name).to_zarr(full_path, mode="w")
            
            # Calculate content hash (SHA-256) of the Zarr directory
            content_hash = self._calculate_dir_hash(full_path)
            
            # Register in catalog
            derived = DerivedVariable(
                id=f"{spec_hash}_{var_name}",
                name=var_name,
                grid_id=grid.id,
                role=derivation.role,
                times=[ctx.source.time] if ctx.source.time is not None else [],
                dtype=str(da.dtype),
                derivation_id=spec_hash,
                spec_hash=spec_hash,
                content_hash=content_hash,
                asset_url=full_path
            )
            self.catalog.save_derived(derived)
            
        return ctx

    def _calculate_dir_hash(self, path: str) -> str:
        """
        Calculates SHA-256 of a directory by hashing all file contents.
        """
        import hashlib
        from pathlib import Path
        
        hasher = hashlib.sha256()
        root = Path(path)
        
        # Sort files to ensure deterministic hash
        for file in sorted(root.rglob("*")):
            if file.is_file():
                # Hash relative path to capture structure changes
                hasher.update(str(file.relative_to(root)).encode())
                with open(file, "rb") as f:
                    # Read in chunks for memory efficiency
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
        
        return hasher.hexdigest()
