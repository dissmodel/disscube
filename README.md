# DissCube

**Declarative Spatial Layer for Dynamic Models**

DissCube is a component of the DisSModel ecosystem designed to represent, derive, and serve multiscale spatial variables for dynamic Land Use and Cover Change (LUCC) models.

## Features

- **Notebook-first**: Designed for interactive research.
- **Declarative**: Define spatial derivations in a structured way.
- **Reproducible**: Stable hashing (`spec_hash`) ensures results are consistent.
- **Local-first**: Works on your machine without complex infrastructure.
- **Zarr-powered**: Efficient storage and access for multidimensional variables.

## Core Concepts

- `GridSpec`: Defines the target spatial extent and resolution.
- `SpatialSource`: References raw raster or vector assets.
- `SpatialRelation`: Defines how a grid relates to another (e.g., multiscale coupling).
- `SpatialDerivation`: Declares how to transform a `SpatialSource` into variables for a `GridSpec`.
- `DerivedVariable`: The resulting variable, ready to be used by a model.

## Integration

DissCube integrates directly with `dissmodel` executors via `to_lucc_data()`.
