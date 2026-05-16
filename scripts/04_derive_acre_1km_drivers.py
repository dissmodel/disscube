"""
scripts/04_derive_acre_1km_drivers.py

Deriva drivers espaciais para a grade de alta resolução do Acre (AC/1km):
  - dist_cidades   → distância mínima aos centros urbanos (PNLT)
"""

from disscube.client import CubeClient
from disscube.models import SpatialDerivation, Variable

GRID_ID = "AC/1km"

# 1. Inicializa o cliente
cube = CubeClient(catalog="catalog.db", store="./data/")

# Verificação de sanidade
grid = cube.catalog.get_grid(GRID_ID)
if grid is None:
    raise RuntimeError(f"Grade {GRID_ID!r} não encontrada. Execute tools/create_acre_1km_grid.py primeiro.")
print(f"[ok] processando grade {GRID_ID} ({grid.rows} x {grid.cols} células)")

# 2. Derivação Temporal (2000-2014 e 2015-2025)
periods = [
    ("2000", "2014"),
    ("2015", "2025")
]

for start, end in periods:
    print(f"\n--- Distância a cidades ({start}-{end}) @ 1km ---")
    derivation = SpatialDerivation(
        source_id="urban_centers",
        grid_id=GRID_ID,
        role="driver",
        variables=[
            Variable(name="dist_cidades", operator="min_distance"),
        ],
        valid_from=start,
        valid_until=end
    )
    print(f"  [derive] spec_hash: {derivation.spec_hash()}")
    cube.derive(derivation)

print("\n=== Derivações 1km para o Acre concluídas ===")
results = cube.search(grid=GRID_ID, role="driver")
for r in results:
    times_str = f"times={r.times}" if r.times else "static"
    print(f"  {r.name:20s}  {times_str:15s}  hash={r.content_hash[:12]}")
