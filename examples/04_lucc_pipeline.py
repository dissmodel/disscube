
from disscube.client import CubeClient
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable

cube = CubeClient(catalog="catalog.json", store="./data/")

# 1. Registrar Grade do Acre (Métrica - 5km)
grid_spec = GridSpec(
    id="AC/5km-métrica",
    type="local",
    crs="EPSG:29101",
    resolution=5000.0,
    bbox=[-1875000.0, -1260000.0, -1050000.0, -815000.0],
    description="Acre Metric Grid"
)
cube.register_grid(grid_spec)

# 2. Registrar Fonte Vetorial (Com o CRS correto)
data_source = SpatialSource(
    id="acre_base_metric",
    name="Acre Vector Data Metric",
    format="vector",
    asset_url="../disslucc-continuous/examples/data/input/csAC.zip",
    crs="EPSG:29101"
)
cube.register_spatial_source(data_source)

# 3. Declarar Derivação
derivation = SpatialDerivation(
    source_id="acre_base_metric",
    grid_id="AC/5km-métrica",
    role="luc_observation",
    variables=[
        Variable(name="f", operator="attribute"),
        Variable(name="d", operator="attribute")
    ]
)

# 4. Executar
print("Processando dados do Acre (vetor -> cubo)...")
cube.derive(derivation)

# 5. Verificar resultado
variables = ["f", "d"]
print(f"Carregando do cubo: {variables}")
backend = cube.to_lucc_data(variables) # Retorna RasterBackend por padrão

print(f"Backend gerado: {backend.shape}")
print(f"Bandas disponíveis: {backend.band_names()}")

# Estatísticas rápidas
for var in variables:
    arr = backend.get(var)
    print(f"Variável '{var}': min={arr.min()}, max={arr.max()}, mean={arr.mean():.4f}")
