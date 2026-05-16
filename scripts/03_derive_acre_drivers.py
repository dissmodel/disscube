"""
scripts/03_derive_acre_drivers.py

Deriva drivers espaciais especificamente para a grade alinhada do Acre (AC/5km):
  - dist_cidades   → distância mínima aos centros urbanos (PNLT)
"""

from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable

GRID_ID = "AC/5km"

# 1. Inicializa o cliente
cube = CubeClient(catalog="catalog.db", store="./data/")

# Verificação de sanidade — a grade AC/5km deve existir
grid = cube.catalog.get_grid(GRID_ID)
if grid is None:
    raise RuntimeError(
        f"Grade {GRID_ID!r} não encontrada. "
        "Execute tools/create_acre_snapped_grid.py primeiro."
    )
print(f"[ok] processando grade {GRID_ID} ({grid.rows} x {grid.cols} células)")

# 2. Derivação Temporal: Distância a Cidades
# Período 1: 2000 - 2014
print("\n--- Distância a cidades (2000-2014) ---")
derivation_2000 = SpatialDerivation(
    source_id="urban_centers",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="dist_cidades", operator="min_distance"),
    ],
    valid_from="2000",
    valid_until="2014"
)
print(f"  [derive] spec_hash: {derivation_2000.spec_hash()}")
cube.derive(derivation_2000)

# Período 2: 2015 - 2025
print("\n--- Distância a cidades (2015-2025) ---")
derivation_2015 = SpatialDerivation(
    source_id="urban_centers",
    grid_id=GRID_ID,
    role="driver",
    variables=[
        Variable(name="dist_cidades", operator="min_distance"),
    ],
    valid_from="2015",
    valid_until="2025"
)
print(f"  [derive] spec_hash: {derivation_2015.spec_hash()}")
cube.derive(derivation_2015)

print("\n=== Derivações para o Acre concluídas ===")
results = cube.search(grid=GRID_ID, role="driver")
for r in results:
    times_str = f"times={r.times}" if r.times else "static"
    print(f"  {r.name:20s}  {times_str:15s}  hash={r.content_hash[:12]}")
