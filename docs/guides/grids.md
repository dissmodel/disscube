# Working with Custom Grids

While DisSCube is pre-configured for BDC, you can define any grid system for your project.

## Creating a Local Grid

A local grid is usually a small area of interest (AOI) with a specific resolution.

```python
from disscube.models import GridSpec

my_grid = GridSpec(
    id="MyProject/30m",
    type="local",
    crs="EPSG:31983",
    resolution=30.0,
    bbox=[580000, 9700000, 600000, 9720000],
    description="Custom grid for local study area"
)

cube.register_grid(my_grid)
```

## Creating a Master Grid

A master grid is a continental definition. It doesn't need tiles to be registered, but if you want to use the `tile_id` feature, you must register the tiles as `SpatialSource` entities in the catalog.

## Grid Relations

You can relate grids to create hierarchies (e.g., 5km to 25km).

```python
from disscube.models import SpatialRelation

rel = SpatialRelation(
    source_grid_id="br_5km",
    target_grid_id="br_25km",
    strategy="simple"
)
cube.register_relation(rel)
```

This allows the **Aggregator** to automatically know how to upsample or downsample variables between these two grids.
