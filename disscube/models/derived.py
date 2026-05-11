from pydantic import BaseModel

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
