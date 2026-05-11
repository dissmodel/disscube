from fastapi import FastAPI, HTTPException
from typing import List, Optional
from disscube.client import CubeClient
from disscube.models import GridSpec, DataSource, SpatialDerivation, DerivedVariable
from .config import CATALOG_PATH, STORE_PATH

app = FastAPI(title="DissCube API")

cube = CubeClient(CATALOG_PATH, STORE_PATH)

@app.get("/grids", response_model=List[GridSpec])
def list_grids():
    return cube.catalog.list_grids()

@app.post("/grids")
def register_grid(grid: GridSpec):
    cube.register_grid(grid)
    return {"status": "ok"}

@app.get("/sources", response_model=List[DataSource])
def list_sources():
    return cube.catalog.list_sources()

@app.post("/sources")
def register_source(source: DataSource):
    cube.register_source(source)
    return {"status": "ok"}

@app.post("/derive", response_model=List[DerivedVariable])
def derive(derivation: SpatialDerivation):
    try:
        return cube.derive(derivation)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/catalog", response_model=List[DerivedVariable])
def get_catalog(grid: Optional[str] = None, role: Optional[str] = None):
    return cube.search(grid=grid, role=role)

@app.get("/variables/{variable_id}")
def get_variable(variable_id: str):
    # This might return metadata or a redirect to the Zarr asset
    # For now, let's just return the derived variable info
    for d in cube.search():
        if d.id == variable_id or d.name == variable_id:
            return d
    raise HTTPException(status_code=404, detail="Variable not found")
