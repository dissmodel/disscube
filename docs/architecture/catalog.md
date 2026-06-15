# Catálogo e Persistência

O catálogo é o registro de tudo que o sistema conhece. Ele não armazena pixels — apenas metadados, ponteiros e hashes.

## Implementações

A interface é definida pelo `CatalogStore` Protocol (`disscube/catalog/protocol.py`):

| Implementação | Arquivo | Uso |
|---|---|---|
| `SqliteCatalogStore` | `catalog/sqlite_store.py` | Padrão — usado por `CubeClient` |
| `JsonCatalogStore` | `catalog/json_store.py` | Legado / testes simples |

## Schema SQLite

```sql
grids    (id TEXT PRIMARY KEY, data TEXT)          -- GridSpec como JSON
sources  (id TEXT PRIMARY KEY, data TEXT)          -- SpatialSource como JSON
derived  (id, grid_id, spec_hash, tile_id, role, data TEXT)
relations (source_grid_id, target_grid_id, data TEXT)
```

Índices: `idx_derived_grid`, `idx_derived_hash`, `idx_derived_tile`.

Todos os objetos são serializados como JSON no campo `data`. As colunas extraídas (`grid_id`, `spec_hash`, `tile_id`) existem para indexação e busca eficiente — os dados completos estão sempre no JSON.

## Hash de especificação (`spec_hash`)

SHA-256 determinístico da `SpatialDerivation`:

```python
relevant_data = {
    "source_id":   ...,
    "grid_id":     ...,
    "role":        ...,
    "variables":   [...],   # ordenados por nome
    "valid_from":  ...,
    "valid_until": ...,
}
encoded = json.dumps(relevant_data, sort_keys=True).encode("utf-8")
return hashlib.sha256(encoded).hexdigest()
```

**O que muda o hash:**

- Trocar a fonte (`source_id`)
- Trocar a grade (`grid_id`)
- Adicionar/remover/renomear variáveis
- Mudar o operador ou `class_code`
- Mudar `valid_from` / `valid_until`

**O que não muda o hash:**

- A ordem das variáveis na lista (são ordenadas por nome)
- `bbox` de `Derivation` (metadado descritivo, não parâmetro)
- `SpatialRelation` — relações são persistidas no catálogo mas excluídas do hash porque nenhum estágio do pipeline as usa durante a computação. Incluí-las tornaria a chave de cache sensível a metadados que não afetam o resultado.

## Hash de conteúdo (`content_hash`)

SHA-256 de todos os bytes dos arquivos do diretório Zarr, em ordem determinística (`sorted(root.rglob("*"))`). Garante integridade do dado materializado independente do `spec_hash`.

## Séries temporais

O campo `times` em `DerivedVariable` é uma lista de inteiros (anos):

- `times = []` → variável estática
- `times = [2020]` → fatia temporal de 2020

`CubeClient.load()` detecta automaticamente se há múltiplas fatias e as empilha em `(time, y, x)` ordenadas pelo primeiro valor de `times`.

`CubeClient.to_lucc_data()` aceita `period=("2000", "2020")` para filtrar apenas as fatias dentro do intervalo.

## Busca no catálogo

```python
# Por grade e role
cube.catalog.search_derived_variables(grid_id="AC/5km", role="driver")

# Por tile
cube.catalog.search_derived_variables(tile_id="009002")

# Por spec_hash (exato)
cube.catalog.get_derived_by_hash("a3f9...")

# Remover entrada por ID
cube.catalog.delete_derived("a3f9..._slope")
```

## Limpeza de entradas órfãs

O catálogo acumula entradas cujos arquivos Zarr foram deletados (comum ao apagar o store para re-testar). `purge_stale()` remove essas entradas:

```python
n = cube.purge_stale()   # retorna o número de entradas removidas
print(f"Removidas {n} entradas órfãs")
```

`load()` já ignora silenciosamente entradas sem arquivo no disco — `purge_stale()` é uma limpeza explícita para manter o catálogo enxuto.

## Evolução do schema

O schema usa `CREATE TABLE IF NOT EXISTS` — seguro para idempotência. Novas colunas exigem `ALTER TABLE` ou migração manual. Os campos descritivos extras de modelos (como `purity_threshold` de `Derivation`) vivem apenas no modelo Python, não no banco — isso protege a compatibilidade retroativa para campos reservados.
