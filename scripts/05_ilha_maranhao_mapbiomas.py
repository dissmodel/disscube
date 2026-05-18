from disscube.client import CubeClient
from disscube.models import SpatialSource, SpatialDerivation
from disscube.models.variable import Variable
from disscube.utils.grids import register_local_grid

# ── 1. Cliente ───────────────────────────────────────────────────────────────
cube = CubeClient(
    catalog="catalog.db",
    store="data/",
)

# ── 2. Grade local snapped na malha BDC 100m ─────────────────────────────────
# bbox_geo vem dos bounds reais do arquivo, com pequena folga
# O snap vai produzir: [6063200, 11008800, 6108200, 11054300] em BDC Albers
# Grid resultante: 455 linhas × 450 colunas = 204.750 células
grid = register_local_grid(
    cube,
    name="ilha_maranhao",
    bbox_geo=(-44.42, -2.80, -44.02, -2.40),  # lon_min, lat_min, lon_max, lat_max
    resolution=100,
    snap=True,
)
# grid.id == "ilha_maranhao/100m"

# ── 3. Fonte bruta ───────────────────────────────────────────────────────────
# nodata=None no arquivo — MapBiomas usa 0 como "sem classificação"
# Declaramos crs e deixamos bbox=None (o GridAligner usa a bbox da grade)
source = SpatialSource(
    id="mapbiomas_ilha_ma_2022",
    name="MapBiomas Ilha do Maranhão — Coleção 2022",
    format="raster",
    asset_url="data/raw/ilha_maranhao_mapbiomas_2022.tif",
    crs="EPSG:4326",
    time=2022,           # entra em DerivedVariable.times=[2022]
    band_map={},         # banda única — sem necessidade de mapeamento
)
cube.register_spatial_source(source)

# ── 4. Derivação ─────────────────────────────────────────────────────────────
# operator="majority" → Resampling.mode no GridAligner (correto para categórico)
# valid_from/valid_until=None → variável estática; o ano vem de source.time
derivation = SpatialDerivation(
    source_id="mapbiomas_ilha_ma_2022",
    grid_id="ilha_maranhao/0km",
    role="land_use",
    variables=[
        Variable(name="uso_2022", operator="majority"),
    ],
)

# ── 5. Pipeline ──────────────────────────────────────────────────────────────
# Normalizer  → abre TIF só para validar (lazy, não carrega)
# GridAligner → reproject EPSG:4326 → BDC Albers, Resampling.mode, 455×450
# Aggregator  → ZonalAggregator, raster banda única → Dataset("uso_2022")
# Writer      → salva Zarr + content_hash + registra DerivedVariable no catálogo
derived = cube.derive(derivation)
print(derived[0])

# ── 6. Inspeciona resultado ──────────────────────────────────────────────────
da = cube.load("uso_2022", grid_id="ilha_maranhao/0km")
print(da)
print("Shape:", da.shape)           # esperado: (455, 450)
print("dtype:", da.dtype)           # uint8
print("Classes presentes:", sorted(set(da.values.flatten().tolist())))