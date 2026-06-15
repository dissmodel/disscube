# Estágios do Pipeline

O pipeline é uma sequência de `PipelineStage`, cada um recebendo e retornando um `PipelineContext`. O contexto carrega fonte, grade, derivação e o dado em transformação.

```python
class PipelineStage:
    def execute(self, ctx: PipelineContext) -> PipelineContext:
        raise NotImplementedError
```

```python
class PipelineContext(BaseModel):
    source: SpatialSource
    grid: GridSpec
    derivation: SpatialDerivation
    tile_id: str | None = None
    data: Any = None
```

A sequência executada por `CubeClient.derive()`:

```python
pipeline = [Normalizer(), GridAligner(), Aggregator(), VariableWriter(store, catalog)]
for stage in pipeline:
    ctx = stage.execute(ctx)
```

---

## 1. Normalizer

**Arquivo:** `disscube/pipeline/normalizer.py`

**Responsabilidade:** ponto de entrada da fonte de dados.

### Raster
Abre o arquivo com `rasterio` para validar que é legível. Não carrega dados — a leitura real é lazy em `GridAligner`.

### Vetor
Carrega o `GeoDataFrame` completo com `geopandas.read_file()`. Se o CRS declarado na fonte (`SpatialSource.crs`) difere do CRS no arquivo, aplica `set_crs(..., allow_override=True)` com `log.warning` explícito.

!!! warning "Override de CRS"
    O `Normalizer` **não reprojeta** — ele apenas corrige metadados. Isso é intencional para fontes com `.prj` malformado ou ausente. Se a intenção é reprojetar, use `SpatialSource.crs` com o CRS real do dado e deixe o `GridAligner` fazer a reprojection.

---

## 2. GridAligner

**Arquivo:** `disscube/pipeline/aligner.py`

**Responsabilidade:** alinhar a fonte ao `GridSpec` alvo.

### Raster — por variável

Para cada variável na derivação:

1. **Seleção de banda:** por `band_map` (1-based) ou por índice posicional.
2. **Resampling por operador:** consulta `OPERATOR_REGISTRY[var.operator].resampling()`. Cada variável usa o método correto para sua semântica (`Resampling.mode` para `majority`, `Resampling.average` para `mean`).
3. **Reprojeção:** `band.rio.reproject(grid.crs, shape=(rows, cols), transform=grid.transform, resampling=...)`.
4. **Invariante de alinhamento:** verifica `aligned.rio.shape == (grid.rows, grid.cols)`. Mismatch → `ValueError` explícito.

Retorna `xr.Dataset` com uma `DataArray` por variável, já com `dims=("y", "x")`.

### Vetor

1. Reprojeta o GeoDataFrame para o CRS da grade usando `pyproj.CRS.equals()` para comparação robusta.
2. Clipa ao bbox da grade com `shapely.geometry.box`.

Retorna o GeoDataFrame processado em `ctx.data`.

### Por que por variável?

Derivações multi-variável de fontes multi-banda frequentemente usam operadores diferentes:

```python
variables=[
    Variable(name="uso",  operator="majority"),  # Resampling.mode
    Variable(name="alt",  operator="mean"),       # Resampling.average
    Variable(name="solo", operator="majority"),   # Resampling.mode
]
```

Com a abordagem por variável, cada banda é reprojetada com o método semanticamente correto. A versão anterior usava apenas `variables[0].operator` para todo o raster.

---

## 3. Aggregator

**Arquivo:** `disscube/pipeline/aggregator.py`

**Responsabilidade:** derivar cada variável chamando seu operador.

Para cada variável na derivação:

```python
op_cls = OPERATOR_REGISTRY[var.operator]

# Raster: ctx.data é Dataset → seleciona DataArray pré-alinhado
# Vetor:  ctx.data é GeoDataFrame → operador faz a rasterização
var_data = ctx.data[var.name] if isinstance(ctx.data, xr.Dataset) else ctx.data

result = op_cls().compute(var_data, var, grid)
final_ds[var.name] = result
```

Não contém nenhuma lógica de operador — é puro despacho. O `if/elif` histórico foi eliminado.

Monta o `xr.Dataset` final. `write_crs()` e `write_transform()` são chamados **depois** do loop de variáveis — rioxarray propaga `grid_mapping="spatial_ref"` apenas para as data variables já presentes no Dataset no momento da chamada. Chamar antes do loop resultaria em nenhuma variável recebendo o atributo, impedindo que leitores CF (QGIS, GDAL) detectem a projeção automaticamente. O CRS é nomeado explicitamente para evitar `PROJCS["unknown"]` em CRSs sem código EPSG registrado (ex: BDC Albers).

---

## 4. VariableWriter

**Arquivo:** `disscube/pipeline/writer.py`

**Responsabilidade:** persistir e registrar.

Para cada variável no Dataset:

1. Adiciona atributos: `grid_id`, `role`, `spec_hash`, `crs`, `tile_id`.
2. Salva como Zarr em `data/derived/{grid_id}/{partition}/{spec_hash}/{var}.zarr`.
3. Calcula `content_hash` (SHA-256 de todos os bytes do Zarr, em ordem determinística).
4. Determina `times`:
   - Se `source.time` está definido → `[source.time]` (ex: MapBiomas 2020)
   - Caso contrário, se `valid_from` é um ano → `[int(valid_from)]`
   - Sem informação temporal → `[]` (variável estática)
5. Registra `DerivedVariable` no catálogo SQLite.

### Tile detection

Se `tile_id` não é passado explicitamente e `grid.id` começa com `BDC_`, tenta extrair o tile do `source.id` (convenção `BDC_LG_009002`). Isso é um fallback para compatibilidade com o workflow BDC.

---

## Idempotência e cache

`CubeClient.derive()` verifica o cache antes de executar:

```python
spec_hash = derivation.spec_hash()
cached_vars = [
    d for d in all_derived
    if d.spec_hash == spec_hash and self.store.fs.exists(d.asset_url)
]
if expected == cached_names:
    return cached_vars   # retorna sem executar o pipeline
```

Reexecutar a mesma derivação é seguro e rápido.
