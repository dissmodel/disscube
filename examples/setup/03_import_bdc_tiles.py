"""
examples/setup/03_import_bdc_tiles.py

Importa os tiles BDC (SM / MD / LG) como SpatialSources no catálogo.
Operação one-time; pode demorar alguns minutos dependendo do tamanho dos
shapefiles.

Pré-requisito:
  - python examples/setup/01_init_catalog.py

Usage:
    python examples/setup/03_import_bdc_tiles.py
"""

from disscube.client import CubeClient
from disscube.utils.bdc_importer import import_bdc_grids


def main():
    cube = CubeClient(catalog="catalog.db", store="./data/")

    print("=== Importando tiles BDC (one-time, pode ser lento) ===")
    import_bdc_grids(
        cube,
        sm_path="zip://data/bdc_grids/BDC_SM_V2.zip",
        md_path="zip://data/bdc_grids/BDC_MD_V2.zip",
        lg_path="zip://data/bdc_grids/BDC_LG_V2.zip",
    )
    print("=== Tiles BDC registrados ===")


if __name__ == "__main__":
    main()
