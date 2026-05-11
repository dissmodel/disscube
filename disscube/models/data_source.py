from typing import Literal
from pydantic import BaseModel

class DataSource(BaseModel):
    id: str
    name: str
    format: Literal["raster", "vector"]
    asset_url: str
    checksum: str | None = None
    crs: str
    time: int | None = None
    tags: list[str] = []
    band_map: dict[str, int] = {}  # variable_name -> band_index (1-based), optional
