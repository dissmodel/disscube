# Grades e Interoperabilidade Espacial

## O problema que as grades snappadas resolvem

Em workflows GIS tradicionais, criar uma grade para o Acre e outra para o Brasil frequentemente produz pixels desalinhados — o canto de um pixel de 5km do Acre não coincide com o canto de um pixel de 5km do Brasil. Agregar de uma grade para outra gera erros por pixels parciais nas bordas.

DisSCube resolve isso com **snap ao mesh virtual**: toda grade local é ancorada à mesma origem do CRS, garantindo que pixels de resoluções múltiplas sempre se alinhem perfeitamente.

## Grades de referência nacionais

```python
from disscube.utils.grids import register_simulation_grids

register_simulation_grids(cube)
# Registra:
#   BR/5km  — 5000 m, BDC Albers, bbox nacional
#   BR/1km  — 1000 m, BDC Albers, bbox nacional
```

## Grades locais com snap

```python
from disscube.utils.grids import register_local_grid

grid = register_local_grid(
    cube,
    name="AC",                            # ou state="AC"
    bbox_geo=(-73.99, -11.15, -66.62, -7.11),  # lon_min, lat_min, lon_max, lat_max
    resolution=5_000.0,
    snap=True,                            # padrão
)
# Produz grade "AC/5km" em BDC Albers
```

**O que `snap=True` faz:**

A bbox geográfica é convertida para BDC Albers e os limites são arredondados para o múltiplo mais próximo da resolução:

```python
minx = math.floor(minx / resolution) * resolution
maxx = math.ceil(maxx  / resolution) * resolution
```

Resultado: `AC/5km` e `BR/5km` têm pixels idênticos na área de sobreposição — um pixel de 5km do Acre é o mesmo quadrado geográfico que o pixel de 5km do Brasil.

## Hierarquia de resoluções

Resoluções múltiplas dentro do mesmo CRS formam uma hierarquia perfeita:

```
1 pixel de 5km
├── 25 pixels de 1km (5×5)
└── 2500 pixels de 100m (50×50)
```

Isso permite **agregação zero-erro**: ao calcular `percentage` de floresta (100m) dentro de uma célula de modelo (5km), todos os pixels de 100m que compõem a célula de 5km são conhecidos exatamente.

## Relações espaciais

`SpatialRelation` registra a relação pai-filho entre grades:

```python
from disscube.models import SpatialRelation

cube.register_relation(SpatialRelation(
    source_grid_id="AC/1km",
    target_grid_id="AC/5km",
    strategy="simple",
))
```

**Estratégias disponíveis** (reservadas para uso futuro no pipeline):

| Estratégia | Uso pretendido |
|---|---|
| `simple` | Grades nested — sem ambiguidade na agregação |
| `chooseone` | Células que pertencem a apenas uma grade-alvo |
| `keepinboth` | Células mantidas em ambas as grades (sobreposição) |

!!! note "Status das estratégias"
    As estratégias estão modeladas no schema mas ainda não são aplicadas pelo pipeline de derivação. São reservadas para o mecanismo de cross-scale do DisSModel.

## Criação manual de grade

Quando o snap ao mesh BDC não é necessário (ex: projeto com CRS local):

```python
from disscube.models import GridSpec

grid = GridSpec(
    id="projeto_local/30m",
    type="local",
    crs="EPSG:31983",
    resolution=30.0,
    bbox=[580000.0, 9700000.0, 600000.0, 9720000.0],
    description="Grade manual sem snap ao mesh nacional",
)
cube.register_grid(grid)
```

!!! warning
    Grades sem snap podem não alinhar com grades nacionais. A agregação cruzada entre grades não-alinhadas introduz erros por pixels parciais.

## Propriedades derivadas de `GridSpec`

```python
grid = GridSpec(id="G", type="local", crs="EPSG:31982", resolution=100, bbox=[0,0,1000,1000])

grid.rows        # 10
grid.cols        # 10
grid.transform   # Affine (North-up, origem no canto superior esquerdo)
grid.xs          # array de centróides X de cada coluna
grid.ys          # array de centróides Y de cada linha

# Identificação de células
cell = grid.cell_id(row=3, col=7)          # "G:R0003C0007"
x, y = grid.coords_from_cell_id(cell)     # centróide em coordenadas do CRS
```
