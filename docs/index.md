# DisSCube Documentation

Welcome to the DisSCube documentation. DisSCube is the geospatial data engine for the **DisSModel** ecosystem.

## Documentation Structure

- **[Architecture](architecture/overview.md)**: Deep dive into how DisSCube works, its pipeline, and the SQLite catalog system.
- **[Guides](guides/bdc.md)**: Practical examples on how to use DisSCube with Brazil Data Cube tiles and custom grids.

## Quick Install

```bash
pip install -r requirements.txt
```

## Core Workflow

1. **Register** your grids and raw data sources in the catalog.
2. **Define** a declarative `SpatialDerivation`.
3. **Execute** the derivation to generate Zarr cube variables.
4. **Load** the variables for analysis or modeling.
