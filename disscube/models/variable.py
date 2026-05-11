import json
import hashlib
from typing import Literal
from pydantic import BaseModel
from .grid import SpatialRelation

class Variable(BaseModel):
    name: str
    operator: str
    class_code: int | None = None

class SpatialSource(BaseModel):
    id: str
    name: str
    format: Literal["raster", "vector"]
    asset_url: str
    checksum: str | None = None
    crs: str
    time: int | None = None
    tags: list[str] = []
    band_map: dict[str, int] = {}  # variable_name -> band_index (1-based), optional

class DerivedVariable(BaseModel):
    id: str
    name: str
    grid_id: str
    role: str
    times: list[int]
    dtype: str
    units: str | None = None
    derivation_id: str
    spec_hash: str
    content_hash: str | None = None
    asset_url: str

class SpatialDerivation(BaseModel):
    source_id: str
    grid_id: str
    role: str
    variables: list[Variable]
    relations: list[SpatialRelation] = []

    def spec_hash(self) -> str:
        """
        Deterministic SHA-256 hash of the derivation spec.
        """
        variables_data = [
            v.model_dump() for v in sorted(self.variables, key=lambda x: x.name)
        ]
        
        relations_data = []
        for r in sorted(self.relations, key=lambda x: (x.source_grid_id, x.target_grid_id, x.strategy)):
            r_dict = r.model_dump()
            r_dict.pop("metadata", None)
            relations_data.append(r_dict)

        relevant_data = {
            "source_id": self.source_id,
            "grid_id": self.grid_id,
            "role": self.role,
            "variables": variables_data,
            "relations": relations_data
        }
        
        encoded = json.dumps(relevant_data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
