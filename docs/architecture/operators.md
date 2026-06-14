# Sistema de Operadores

DisSCube implementa operadores como classes Python auto-registradas. Adicionar um novo operador não requer nenhuma mudança no pipeline.

## Como funciona

Toda subclasse de `Operator` que define `name` é inserida automaticamente no `OPERATOR_REGISTRY` via `__init_subclass__`:

```python
# operators/base.py
class Operator:
    name: ClassVar[str]
    requires_class_code: ClassVar[bool] = False
    _resampling: ClassVar[Resampling] = Resampling.nearest

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "name"):
            OPERATOR_REGISTRY[cls.name] = cls   # auto-registro

    @classmethod
    def resampling(cls) -> Resampling:
        return cls._resampling

    def compute(self, data, var, grid) -> xr.DataArray:
        raise NotImplementedError
```

O `GridAligner` consulta `op_cls.resampling()` para escolher o método de reamostragem antes de reprojetar o raster. O `Aggregator` chama `op_cls().compute(data, var, grid)` para calcular o resultado. Nenhum dos dois contém listas de operadores.

## Operadores disponíveis

### Zonais — raster e vetor

| Operador | `_resampling` | Raster | Vetor | `requires_class_code` |
|---|---|---|---|---|
| `mean` | `average` | média dos pixels no upscale | — | não |
| `sum` | `sum` | soma dos pixels no upscale | — | não |
| `std` | `nearest` | valor reamostrado¹ | — | não |
| `min` | `min` | mínimo no upscale | — | não |
| `max` | `max` | máximo no upscale | — | não |
| `majority` | `mode` | moda no upscale | rasteriza com `class_code` (ou 1) | não |
| `minority` | `mode` | moda no upscale | rasteriza com `class_code` (ou 1) | não |
| `percentage` | `mode` | valor reamostrado¹ | rasteriza com `class_code` | **sim** |
| `attribute` | `nearest` | passthrough | rasteriza com valor da coluna `var.name` | não |
| `presence` | `nearest` | passthrough | rasteriza com `class_code` (ou 1) binário | não |

¹ `std` e `percentage` para rasters usam o dado já reamostrado pelo `GridAligner` — estatísticas verdadeiras de janela (como `rasterstats`) são trabalho futuro.

### Proximidade — vetor (e passthrough para raster)

| Operador | Descrição | `requires_class_code` |
|---|---|---|
| `min_distance` | Distância euclidiana (em unidades do CRS) até a feature mais próxima | não |
| `count` | Contagem de features cujo centroide cai em cada célula | não |

## Contrato de `compute()`

```python
def compute(
    self,
    data: xr.DataArray | gpd.GeoDataFrame,
    var: Variable,
    grid: GridSpec,
) -> xr.DataArray:
```

- `data`: para fontes raster, é o `DataArray` já reprojetado e reamostrado pelo `GridAligner`; para vetores, é o `GeoDataFrame` reprojetado e clipado ao bbox.
- Retorno: `xr.DataArray` com `dims=("y", "x")` e `coords` alinhados a `grid.ys` / `grid.xs`.

## Adicionar um operador novo

Crie o arquivo `disscube/operators/meu_operador.py`:

```python
from rasterio.warp import Resampling
import xarray as xr
import numpy as np
from disscube.operators.base import Operator

class WeightedMeanOperator(Operator):
    """Média ponderada pela área de interseção (exemplo ilustrativo)."""
    name = "weighted_mean"
    _resampling = Resampling.average  # usado pelo GridAligner

    def compute(self, data, var, grid) -> xr.DataArray:
        if isinstance(data, xr.DataArray):
            if "band" in data.dims:
                data = data.isel(band=0)
            return data.transpose("y", "x")
        raise TypeError(f"'weighted_mean' requer fonte raster")
```

Importe o módulo para que o `__init_subclass__` seja executado — basta adicionar ao `disscube/operators/__init__.py`:

```python
from . import meu_operador  # noqa: F401
```

Pronto. O operador aparece em `OPERATOR_REGISTRY["weighted_mean"]` e é aceito em `Derivation(operator="weighted_mean")` e em `Variable(operator="weighted_mean")`.

## `attribute` — contrato implícito

O operador `attribute` rasteriza um vetor usando o valor de uma coluna numérica como pixel value. **A coluna deve ter o mesmo nome que a variável (`Variable.name`)**:

```python
# Fonte vetor com coluna "f" e coluna "d"
Variable(name="f", operator="attribute")   # usa gdf["f"]
Variable(name="d", operator="attribute")   # usa gdf["d"]
```

Se a coluna não existir no GeoDataFrame, o resultado é um raster de zeros sem erro explícito. Garanta que o nome da variável corresponda ao nome da coluna na fonte.

## Validação em construção (`Derivation`)

`Derivation` valida o nome do operador e os campos obrigatórios no momento da criação:

```python
# Erro imediato — operador inexistente
Derivation(target="x", source_id="s", operator="bogus")
# ValueError: Unknown operator 'bogus'. Available: ['attribute', 'count', ...]

# Erro imediato — percentage sem class_code
Derivation(target="x", source_id="s", operator="percentage")
# ValueError: Operator 'percentage' requires class_code to be set.
```

`SpatialDerivation` e `Variable` não validam — o erro aparece no `Aggregator` em tempo de execução. Use `Derivation` para validação antecipada.
