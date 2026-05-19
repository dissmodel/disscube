from disscube.client import CubeClient
from disscube.models import SpatialSource, SpatialDerivation
from disscube.models.variable import Variable
from disscube.utils.grids import register_local_grid
import os

# ── 1. Cliente ───────────────────────────────────────────────────────────────
cube = CubeClient(
    catalog="catalog.db",
    store="data/",
)

# ── 2. Grade local ───────────────────────────────────────────────────────────
grid = register_local_grid(
    cube,
    name="ilha_maranhao",
    bbox_geo=(-44.42, -2.80, -44.02, -2.40),
    resolution=100,
    snap=True,
)

# ── 3. Processamento Temporal (Loop de Anos) ─────────────────────────────────
# Para MapBiomas, geralmente temos uma série temporal. 
# Aqui exemplificamos como registrar e derivar múltiplos anos.

years = [2010, 2022]
for year in years:
    asset = f"data/raw/ilha_maranhao_mapbiomas_{year}.tif"
    
    # Registro da Fonte
    source_id = f"mapbiomas_ilha_ma_{year}"
    source = SpatialSource(
        id=source_id,
        name=f"MapBiomas Ilha do Maranhão — {year}",
        format="raster",
        asset_url=asset,
        crs="EPSG:4326",
        time=year,           # Define este dado como temporal no cubo
    )
    cube.register_spatial_source(source)

    # Registro da Derivação
    # O spec_hash será diferente para cada ano pois o source_id muda
    derivation = SpatialDerivation(
        source_id=source_id,
        grid_id="ilha_maranhao/100m",
        role="land_use",
        variables=[
            Variable(name="uso", operator="majority"),
        ],
    )
    
    print(f"\n[pipeline] Processando ano {year}...")
    cube.derive(derivation)

# ── 4. Distância a Sedes (Variável Estática) ─────────────────────────────────
derivation_sedes = SpatialDerivation(
    source_id="urban_centers",
    grid_id="ilha_maranhao/100m",
    role="driver",
    variables=[
        Variable(name="dist_sedes", operator="min_distance"),
    ],
)
print("\n[pipeline] Processando distância a sedes...")
cube.derive(derivation_sedes)

# ── 5. Carregamento do Cubo ──────────────────────────────────────────────────
# Ao carregar "uso", o Cubo detecta que existem múltiplos anos e retorna (time, y, x)
da_uso = cube.load("uso", grid_id="ilha_maranhao/100m")
print("\n=== Dados Temporais (uso) ===")
print(da_uso.dims, da_uso.coords["time"].values)

# Ao carregar "dist_sedes", ele retorna (y, x) por ser estática
da_sedes = cube.load("dist_sedes", grid_id="ilha_maranhao/100m")
print("\n=== Dados Estáticos (dist_sedes) ===")
print(da_sedes.dims, da_sedes.shape)

# ── 6. Integração com DisSModel (Backend Misto) ──────────────────────────────
# O backend resultante terá um eixo de tempo para "uso" e será estático para "dist_sedes"
backend = cube.to_lucc_data(["uso", "dist_sedes"], grid_id="ilha_maranhao/100m")

print("\n=== Integração DisSModel Temporal ===")
print(f"Backend: {backend}")
print(f"É temporal? uso={backend.is_temporal('uso')}, dist_sedes={backend.is_temporal('dist_sedes')}")

# No dissmodel, você pode acessar um ano específico do backend
data_2010 = backend.get("uso", time=2010)
print(f"Shape do slice de 2010: {data_2010.shape}")

# Ou filtrar um período específico na carga do cubo
backend_filtered = cube.to_lucc_data(
    ["uso"], 
    grid_id="ilha_maranhao/100m", 
    period=(2022, 2022)
)
print(f"Anos no backend filtrado: {backend_filtered.temporal_band_names()}")

