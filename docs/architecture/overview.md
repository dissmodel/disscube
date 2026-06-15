# Visão Geral da Arquitetura

DisSCube implementa uma abstração de alto nível para construção de cubos de dados espaciais derivados de múltiplas fontes geoespaciais. Ao contrário de um conjunto de scripts GIS, o sistema trata **derivações como objetos declarativos** com identidade, rastreabilidade e reprodutibilidade garantidas.

## Modelo conceitual

```
SpatialSource ──► SpatialDerivation ──► Variable ──► DerivedVariable
     │                    │
  asset_url            spec_hash (SHA-256)
  format               grid_id
  crs                  valid_from / valid_until
```

### Entidades principais

| Entidade | Papel |
|---|---|
| `GridSpec` | Definição matemática do espaço: CRS + resolução + bbox |
| `SpatialSource` | Ponteiro para dado bruto: raster (GeoTIFF) ou vetor (GPKG/SHP) |
| `SpatialDerivation` | Intenção de derivação: fonte + grade + operadores + janela temporal |
| `Derivation` | Front-end declarativo sobre `SpatialDerivation` com validação em construção |
| `Variable` | Nome + operador + class_code para uma variável derivada |
| `DerivedVariable` | Produto materializado: path Zarr + `spec_hash` + `content_hash` |
| `SpatialRelation` | Relação pai-filho entre grades (reservado para futuro uso no pipeline) |

### Dois modos de uso

**Declarativo (recomendado):**
```python
from disscube.derivation import Derivation

d = Derivation(
    target="forest_pct",
    source_id="mapbiomas_2020",
    operator="percentage",
    class_code=3,
    valid_from="2020", valid_until="2020",
)
cube.derive_declarative(d, grid_id="AC/5km")
```
Valida o operador e `class_code` na construção (fail-fast), antes de qualquer I/O.

**Direto:**
```python
from disscube.models import SpatialDerivation, Variable

cube.derive(SpatialDerivation(
    source_id="mapbiomas_2020", grid_id="AC/5km", role="driver",
    variables=[Variable(name="forest_pct", operator="percentage", class_code=3)],
    valid_from="2020", valid_until="2020",
))
```
Ambos os modos chegam ao mesmo pipeline — `Derivation` é um front-end, não um caminho alternativo.

## Pipeline de execução

```
SpatialSource
    │
    ▼ Normalizer
    │  • raster: valida abertura do arquivo
    │  • vetor: carrega GeoDataFrame, corrige CRS se necessário
    │
    ▼ GridAligner
    │  • raster: reproject por variável com Resampling do operador
    │           → retorna xr.Dataset {var_name: DataArray}
    │  • vetor:  reprojeta GDF + clip ao bbox da grade
    │  • invariante: verifica shape == (grid.rows, grid.cols)
    │
    ▼ Aggregator
    │  • delega a operator.compute(data, var, grid) → DataArray
    │  • monta xr.Dataset final com CRS e transform
    │
    ▼ VariableWriter
       • salva cada variável como Zarr
       • calcula content_hash (SHA-256 dos bytes)
       • registra DerivedVariable no catálogo SQLite
```

## Reprodutibilidade: `spec_hash`

Cada `SpatialDerivation` tem um `spec_hash` — SHA-256 determinístico de:

- `source_id`
- `grid_id`
- `role`
- variáveis (nome + operador + class_code, ordenadas por nome)
- `valid_from` / `valid_until`

`SpatialRelation` é excluída do hash: nenhum estágio do pipeline a usa durante a computação, então incluí-la tornaria o cache sensível a metadados sem efeito no resultado.

Se qualquer parâmetro mudar, o hash muda. O pipeline verifica o cache antes de processar: se todos os `DerivedVariable` com o mesmo `spec_hash` já existem no disco, a derivação é pulada.

`Derivation.spec_hash()` delega a `SpatialDerivation.spec_hash()` e adiciona `purity_threshold` quando definido. `bbox` é excluído — é metadado descritivo, não parâmetro de derivação.

## Sistema de operadores (plugin)

Cada operador é uma subclasse de `Operator` que se auto-registra no `OPERATOR_REGISTRY`:

```python
class MajorityOperator(Operator):
    name = "majority"
    _resampling = Resampling.mode

    def compute(self, data, var, grid) -> xr.DataArray:
        ...
```

`OPERATOR_REGISTRY["majority"]` → `MajorityOperator`. O `GridAligner` usa `op_cls.resampling()` para escolher o método de reamostragem por variável. O `Aggregator` usa `op_cls().compute()` para calcular o resultado. Adicionar um operador = criar um arquivo; zero mudança no pipeline.

Ver [Operadores](operators.md) para a lista completa e guia de extensão.

## Armazenamento

```
data/derived/{grid_id}/{partition}/{spec_hash}/{variable_name}.zarr
```

- `partition` = `tile_id` ou `global`.
- Cada variável é um dataset Zarr independente com `spatial_ref` e metadados CRS.
- `content_hash` (SHA-256 dos bytes do Zarr) garante integridade do dado materializado.
