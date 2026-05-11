from typing import Literal, Tuple
from pydantic import BaseModel
import numpy as np
import re
import warnings
from affine import Affine

class GridAnchor(BaseModel):
    """
    DEPRECATED: Use GridSpec instead.
    This class is kept for backward compatibility only.
    """
    id: str
    crs: str
    resolution: float
    bbox: list[float]

    def __init__(self, **data):
        warnings.warn(
            "GridAnchor is deprecated and will be removed in a future version. Use GridSpec instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(**data)

class SpatialRelation(BaseModel):
    source_grid_id: str
    target_grid_id: str
    strategy: Literal["simple", "chooseone", "keepinboth"]
    params: dict = {}     # ex: {"min_intersection": 0.01} para keepinboth
    metadata: dict = {}   # descrição, referência bibliográfica, etc.

class GridSpec(BaseModel):
    id: str
    type: Literal["local", "global", "reference"]
    crs: str
    resolution: float
    bbox: list[float]  # [minx, miny, maxx, maxy]
    description: str | None = None

    @property
    def rows(self) -> int:
        return int(round((self.bbox[3] - self.bbox[1]) / self.resolution))

    @property
    def cols(self) -> int:
        return int(round((self.bbox[2] - self.bbox[0]) / self.resolution))

    @property
    def transform(self) -> Affine:
        # North-up transform: origin at (minx, maxy), negative y-scale
        return Affine.translation(self.bbox[0], self.bbox[3]) * Affine.scale(self.resolution, -self.resolution)

    @property
    def xs(self) -> np.ndarray:
        return np.arange(self.cols) * self.resolution + self.bbox[0] + self.resolution/2

    @property
    def ys(self) -> np.ndarray:
        return self.bbox[3] - (np.arange(self.rows) * self.resolution + self.resolution/2)

    def to_toml(self) -> str:
        import toml
        return toml.dumps(self.model_dump())

    def cell_id(self, row: int, col: int) -> str:
        """Retorna identificador estável: 'grid_id:R0991C0047'"""
        return f"{self.id}:R{row:04d}C{col:04d}"

    def cell_id_from_coords(self, x: float, y: float) -> str:
        """
        Dado um ponto (x, y) no CRS da grade, retorna o cell_id.

        ATENÇÃO CRÍTICA — origem North-Up:
        Se a bbox usa canto superior esquerdo (north-up), o cálculo de row é:
            row = int((origin_y - y) / resolution)
            col = int((x - origin_x) / resolution)
        """
        minx, miny, maxx, maxy = self.bbox
        if not (minx <= x <= maxx and miny <= y <= maxy):
            raise ValueError(f"Coordinates ({x}, {y}) out of grid bbox {self.bbox}")
        
        row = int((maxy - y) / self.resolution)
        col = int((x - minx) / self.resolution)
        
        # Boundary check for exact maxx/miny which might result in index = num_cells
        num_rows = self.rows
        num_cols = self.cols
        
        if row >= num_rows: row = num_rows - 1
        if col >= num_cols: col = num_cols - 1
        
        return self.cell_id(row, col)

    def coords_from_cell_id(self, cell_id: str) -> tuple[float, float]:
        """Retorna centroide (x, y) da célula no CRS da grade."""
        grid_id, row, col = self.parse_cell_id(cell_id)
        if grid_id != self.id:
            raise ValueError(f"Cell ID {cell_id} does not match grid ID {self.id}")
        
        minx, miny, maxx, maxy = self.bbox
        x = minx + (col + 0.5) * self.resolution
        y = maxy - (row + 0.5) * self.resolution
        return (x, y)

    @staticmethod
    def parse_cell_id(cell_id: str) -> tuple[str, int, int]:
        """Retorna (grid_id, row, col) a partir de um cell_id."""
        try:
            grid_id, coords = cell_id.split(":")
            # Robust parsing using regex to support any number of digits
            match = re.match(r"^R(\d+)C(\d+)$", coords)
            if not match:
                raise ValueError(f"Invalid coordinate format in cell_id: {coords}")
            
            row = int(match.group(1))
            col = int(match.group(2))
            return grid_id, row, col
        except Exception as e:
            if isinstance(e, ValueError) and "Invalid coordinate format" in str(e):
                raise
            raise ValueError(f"Invalid cell_id format: {cell_id}") from e
