# DisSCube

> **Status: Alpha — APIs estáveis para o pipeline principal; modelos declarativos em evolução.**

DisSCube é o motor de cubos de dados espaciais do ecossistema **DisSModel**. Ele converte fontes geoespaciais brutas (rasters, vetores) em variáveis derivadas alinhadas a grades de modelagem LUCC (Land Use and Cover Change), prontas para modelos de Autômatos Celulares e análises espacio-temporais.

## Conceito central

```
SpatialSource  →  Derivation  →  Variable  →  DerivedVariable (Zarr)
```

Uma **fonte** (`SpatialSource`) passa por uma **derivação** (`SpatialDerivation` ou `Derivation`) que aplica um **operador** a uma **grade** (`GridSpec`), produzindo uma **variável derivada** registrada no catálogo SQLite e armazenada em Zarr.

## Instalação

```bash
git clone https://github.com/DisSModel/disscube.git
cd disscube
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Uso básico

### 1. Inicializar catálogo e registrar grade

```python
from disscube.client import CubeClient
from disscube.utils.grids import register_local_grid

cube = CubeClient(catalog="catalog.db", store="./data/")

grid = register_local_grid(
    cube,
    name="AC",
    bbox_geo=(-73.99, -11.15, -66.62, -7.11),
    resolution=5_000.0,
)
```

### 2. Registrar fonte

```python
from disscube.models import SpatialSource

cube.register_spatial_source(SpatialSource(
    id="mapbiomas_2020",
    name="MapBiomas Acre 2020",
    format="raster",
    asset_url="data/raw/mapbiomas_2020.tif",
    crs="EPSG:4326",
    time=2020,
))
```

### 3. Derivar — modo declarativo (recomendado)

```python
from disscube.derivation import Derivation

d = Derivation(
    target="forest_pct",
    source_id="mapbiomas_2020",
    operator="percentage",
    class_code=3,
    role="driver",
    valid_from="2020",
    valid_until="2020",
)

cube.derive_declarative(d, grid_id="AC/5km")
```

### 4. Derivar — modo direto

```python
from disscube.models import SpatialDerivation, Variable

cube.derive(SpatialDerivation(
    source_id="mapbiomas_2020",
    grid_id="AC/5km",
    role="driver",
    variables=[Variable(name="forest_pct", operator="percentage", class_code=3)],
    valid_from="2020",
    valid_until="2020",
))
```

### 5. Carregar resultado

```python
da = cube.load("forest_pct", grid_id="AC/5km")
print(da.shape)   # (rows, cols)
```

### 6. Integrar ao DisSModel

```python
backend = cube.to_lucc_data(
    ["forest_pct", "dist_roads"],
    grid_id="AC/5km",
    period=("2015", "2020"),
)
```

## Operadores disponíveis

| Operador | Tipo | Resampling | Requer `class_code` |
|---|---|---|---|
| `mean` | zonal | average | não |
| `sum` | zonal | sum | não |
| `std` | zonal | nearest | não |
| `min` | zonal | min | não |
| `max` | zonal | max | não |
| `majority` | zonal | mode | não |
| `minority` | zonal | mode | não |
| `percentage` | zonal | mode | **sim** |
| `attribute` | zonal | nearest | não |
| `presence` | zonal | nearest | não |
| `min_distance` | proximity | nearest | não |
| `count` | proximity | nearest | não |

## Pipeline

```
SpatialSource
    │
    ▼
Normalizer        — valida / carrega GeoDataFrame (vetor) ou abre raster
    │
    ▼
GridAligner       — reprojeta por variável com o Resampling correto do operador
    │
    ▼
Aggregator        — delega a operator.compute() → xr.DataArray por variável
    │
    ▼
VariableWriter    — persiste Zarr + registra DerivedVariable no catálogo
```

## Estrutura de armazenamento

```
data/derived/{grid_id}/{partition}/{spec_hash}/{variable_name}.zarr
```

- `partition` = `tile_id` ou `global` para derivações sem tile.
- `spec_hash` = SHA-256 da derivação (fonte + grade + variáveis + janela temporal).

## Estrutura do projeto

```
disscube/
├── client/           CubeClient — ponto de entrada público
├── models/           GridSpec, SpatialSource, SpatialDerivation, Variable…
├── derivation.py     Derivation declarativa (front-end sobre SpatialDerivation)
├── operators/        Operadores como classes (auto-registro via __init_subclass__)
│   ├── base.py       Operator ABC + OPERATOR_REGISTRY
│   ├── zonal.py      mean, sum, majority, percentage, attribute, presence…
│   └── proximity.py  min_distance, count
├── pipeline/         Stages: Normalizer → GridAligner → Aggregator → Writer
├── catalog/          CatalogStore (Protocol) + SQLite e JSON implementations
├── storage/          AssetStore (fsspec — local e S3)
└── utils/grids.py    register_local_grid, register_simulation_grids
```

## Adicionar um operador novo

Crie uma subclasse de `Operator` em qualquer arquivo importado na inicialização:

```python
from rasterio.warp import Resampling
from disscube.operators.base import Operator

class WeightedMeanOperator(Operator):
    name = "weighted_mean"
    _resampling = Resampling.average

    def compute(self, data, var, grid):
        # data é xr.DataArray (raster) ou GeoDataFrame (vetor)
        ...
```

O operador é registrado automaticamente e aceito em `Derivation` / `SpatialDerivation` sem nenhuma outra mudança.

## Limitações conhecidas

As limitações abaixo são decisões de escopo da versão atual, não bugs. Estão documentadas para que usuários e revisores entendam o que está implementado versus o que está planejado.

**Processamento em memória, single-tile**
Cada chamada a `derive()` carrega o dado completo de um tile em memória. Não há processamento lazy (Dask) nem distribuído. Para grades de escala continental (ex: `BR/1km`), use o loop de tiles — cada tile é processado e salvo independentemente.

**Agregação vetorial por rasterização (não área-ponderada)**
Operadores sobre fontes vetoriais (`majority`, `percentage`, `attribute`, `presence`, `minority`) convertem geometrias em raster antes de agregar pixels. A fração de cobertura de cada célula é estimada por contagem de pixels, não por cálculo de área de interseção. Para cobertura proporcional mais precisa, use uma fonte raster em resolução substancialmente maior que a célula-alvo.

**Desambiguação de tiles em `load()`**
`CubeClient.load(name)` sem `tile_id` retorna silenciosamente o primeiro resultado quando múltiplos tiles da mesma variável existem na mesma grade. Erro explícito ou mosaico automático estão planejados. **Especifique sempre `tile_id` em workloads multi-tile.**

**`SpatialRelation` não atua no pipeline**
O modelo `SpatialRelation` é persistido no catálogo, mas nenhum estágio do pipeline usa as relações durante a derivação — e por isso elas são **excluídas do `spec_hash`**. Incluí-las tornaria a chave de cache sensível a metadados que não afetam o resultado, quebrando a garantia de reprodutibilidade. A integração com estratégias hierárquicas de grades está reservada para versão futura.

**`purity_threshold` reservado**
O campo `purity_threshold` em `Derivation` é incluído no `spec_hash`, mas não é aplicado à saída — a máscara por pureza não está implementada. Definir `purity_threshold` muda o cache key sem mudar o resultado.

**Sem integração STAC**
Os campos `valid_from`/`valid_until` e `bbox` em `Derivation` seguem a convenção de nomenclatura STAC, mas nenhuma lógica de cliente, catálogo ou exportação STAC está implementada neste módulo.

## Licença

Parte do ecossistema DisSModel. Ver `LICENSE` para detalhes.
