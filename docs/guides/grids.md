# Working with Custom Grids

While DisSCube is pre-configured for BDC, you can define any grid system for your project.

## 🔗 Snapped State Grids (Interoperability)

For regional projects (e.g., studying land change only in Acre), it is crucial that the local grid is aligned with the national grid (e.g., BDC Brazil 5km). If pixels are not aligned, interoperability between datasets fails without expensive resampling.

DisSCube provides a utility to create **Snapped Grids**:

```python
from disscube.utils.bdc_importer import register_state_grid

# This will:
# 1. Project the geographic AOI to BDC Albers
# 2. Snap the bounds to the nearest 5000m multiples
# 3. Ensure the grid is "pixel-perfect" relative to the BR/5km mesh
grid = register_state_grid(
    cube, 
    state="AC", 
    bbox_geo=(-74, -11, -66, -7), 
    resolution=5000.0
)
```

## Creating a Local Grid (Custom)

A local grid is usually a small area of interest (AOI) with a specific resolution and CRS.

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
    source_grid_id="BR/5km",
    target_grid_id="BR/25km",
    strategy="simple"
)
cube.register_relation(rel)
```

This allows the **Aggregator** to automatically know how to upsample or downsample variables between these two grids.
