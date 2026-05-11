import json
import hashlib
from pydantic import BaseModel
from .grid_spec import SpatialRelation

class Variable(BaseModel):
    name: str
    operator: str
    class_code: int | None = None

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
        # Variables sorted by name to ensure stable hash
        variables_data = [
            v.model_dump() for v in sorted(self.variables, key=lambda x: x.name)
        ]
        
        # Relations sorted and metadata excluded to ensure stable hash
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
        
        # Sort keys to ensure stability
        encoded = json.dumps(relevant_data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
