from disscube.models import GridSpec
from disscube.client import CubeClient
import os

def register_brazil_grid():
    # BDC Albers Equal Area CRS
    bdc_crs = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
    
    # BBox original do Brasil (Full Extent)
    # Alinhada a 5000m (múltiplos exatos de 5000)
    bbox = [2400000.0, 7100000.0, 7400000.0, 12100000.0]
    resolution = 5000.0
    
    grid = GridSpec(
        id="BR/5km",
        type="reference",
        crs=bdc_crs,
        resolution=resolution,
        bbox=bbox,
        description="Brazil 5km National Grid (Aligned with BDC Albers)"
    )
    
    client = CubeClient(catalog="catalog.db", store="./data/")
    print(f"Restaurando Grade Nacional: {grid.id}")
    client.register_grid(grid)
    
    # Summary
    print("-" * 30)
    print(f"Dimensões: {grid.rows} linhas x {grid.cols} colunas")
    print(f"Total de células: {grid.rows * grid.cols}")
    print("-" * 30)

if __name__ == "__main__":
    register_brazil_grid()
