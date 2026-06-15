# DisSCube

DisSCube é o motor de cubos de dados espaciais do ecossistema **DisSModel**. Ele converte fontes geoespaciais brutas em variáveis derivadas alinhadas a grades de modelagem LUCC (Land Use and Cover Change).

## Conceito central

```
SpatialSource  →  Derivation  →  Variable  →  DerivedVariable (Zarr)
```

Uma **fonte** (`SpatialSource`) passa por uma **derivação** que aplica um **operador** a uma **grade** (`GridSpec`), produzindo uma variável registrada no catálogo SQLite e armazenada em Zarr.

## Instalação rápida

```bash
git clone https://github.com/DisSModel/disscube.git
cd disscube
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Fluxo principal

```python
from disscube.client import CubeClient
from disscube.derivation import Derivation

cube = CubeClient(catalog="catalog.db", store="./data/")

d = Derivation(
    target="forest_pct",
    source_id="mapbiomas_2020",
    operator="percentage",
    class_code=3,
    valid_from="2020",
    valid_until="2020",
)
cube.derive_declarative(d, grid_id="AC/5km")

da = cube.load("forest_pct", grid_id="AC/5km")
```

## Navegação

- [**Arquitetura**](architecture/overview.md) — modelo conceitual, pipeline e hash de reprodutibilidade
- [**Operadores**](architecture/operators.md) — sistema de plugins, operadores disponíveis, como adicionar novos
- [**Pipeline**](architecture/pipeline.md) — estágios detalhados: Normalizer → GridAligner → Aggregator → Writer
- [**Catálogo**](architecture/catalog.md) — SQLite, schema, hash e séries temporais
- [**Grades**](guides/grids.md) — snap ao mesh nacional, grades locais, relações espaciais
- [**Guia BDC**](guides/bdc.md) — integração com Brazil Data Cube e processamento por tiles
