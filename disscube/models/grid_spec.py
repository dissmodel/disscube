from typing import Literal, Tuple
from pydantic import BaseModel

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
        num_rows = int(round((maxy - miny) / self.resolution))
        num_cols = int(round((maxx - minx) / self.resolution))
        
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
            row = int(coords[1:5])
            col = int(coords[6:])
            return grid_id, row, col
        except Exception as e:
            raise ValueError(f"Invalid cell_id format: {cell_id}") from e
