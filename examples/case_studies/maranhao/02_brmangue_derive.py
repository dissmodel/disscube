"""
examples/case_studies/maranhao/02_brmangue_derive.py

BR-MANGUE — deriva variáveis de uso do solo para a Ilha do Maranhão (100 m):
  - uso, alt, solo  (majority / mean sobre maranhao_base)

Pré-requisitos:
  - python examples/setup/01_init_catalog.py
  - python examples/setup/02_register_sources.py

Usage:
    python examples/case_studies/maranhao/02_brmangue_derive.py
"""

from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable

GRID_ID   = "ilha_maranhao/100m"
SOURCE_ID = "maranhao_base"
cube = CubeClient(catalog="catalog.db", store="./data/")

if not cube.catalog.get_grid(GRID_ID):
    raise RuntimeError(f"Grade {GRID_ID!r} não encontrada. Execute examples/setup/01_init_catalog.py primeiro.")
if not cube.catalog.get_spatial_source(SOURCE_ID):
    raise RuntimeError(f"Fonte {SOURCE_ID!r} não encontrada. Execute examples/setup/02_register_sources.py primeiro.")

print(f"\n[derive] {SOURCE_ID} @ {GRID_ID}...")
cube.derive(SpatialDerivation(
    source_id=SOURCE_ID,
    grid_id=GRID_ID,
    role="luc_observation",
    variables=[
        Variable(name="uso",  operator="majority"),
        Variable(name="alt",  operator="mean"),
        Variable(name="solo", operator="majority"),
    ],
))

print("\n=== BR-MANGUE derivation complete ===")
