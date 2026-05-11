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
        dump = self.model_dump()
        # Sort keys to ensure stability
        encoded = json.dumps(dump, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
