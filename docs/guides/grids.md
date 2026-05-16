# Grids & Spatial Interoperability

DisSCube is built on a **Universal Grid Architecture**. This allows multiple areas of study and different resolutions to coexist and interact without the need for expensive and lossy resampling.

## 🔗 The "Magic" of Snapped Grids

When you create a local grid (for a state, municipality, or any Area of Interest), DisSCube doesn't just cut the data at the boundaries. It performs a **Snapping** operation.

### What is Snapping?
Snapping ensures that the boundaries of any grid are exact multiples of its resolution, calculated from the origin `(0,0)` of the Coordinate Reference System (CRS).

- **Without Snapping**: A grid starting at `x=2815245.5` with 5km resolution would have pixels shifted relative to a national grid.
- **With Snapping**: DisSCube rounds the start to `x=2815000.0`. 

### Why it matters
Because all grids (National, State, Local) are "pinned" to the same universal virtual mesh, **their pixels always align perfectly**. If you place a 5km pixel of the Acre grid over the 5km pixel of the Brazil grid, they are exactly the same square in the world.

## 📦 Nested Grids (Hierarchy)

Nesting happens when you use resolutions that are multiples of each other (e.g., 5km, 1km, 100m). 

Since they are all snapped to the same origin, the pixels form a perfect hierarchy:
- **1 pixel of 5km** contains exactly **25 pixels of 1km** ($5 \times 5$).
- **1 pixel of 1km** contains exactly **100 pixels of 100m** ($10 \times 10$).

This "magic" allows for **Zero-Error Aggregation**. When calculating the percentage of forest (at 100m resolution) inside a model cell (at 5km), DisSCube knows exactly which $50 \times 50$ small pixels belong to the large cell. There are no "partial pixels" at the edges.

## 🛠 Using `register_local_grid`

To take advantage of this, always use the `register_local_grid` utility:

```python
from disscube.utils.grids import register_local_grid

# Register a 1km grid for Acre that "nests" inside the national 5km grid
grid = register_local_grid(
    cube, 
    name="AC", 
    bbox_geo=(-74, -11, -66, -7), 
    resolution=1000.0,
    snap=True # This is the magic switch (True by default)
)
```

## 🗺 Spatial Relations

`SpatialRelation` entities define how data should move between different grids. Because of the snapping/nesting logic, these relations become much more powerful.

```python
from disscube.models import SpatialRelation

# Define that BR/1km is a child of BR/5km
rel = SpatialRelation(
    source_grid_id="BR/1km",
    target_grid_id="BR/5km",
    strategy="simple" # Because they are nested, "simple" is perfectly accurate
)
cube.register_relation(rel)
```

### Strategies
- **simple**: Used when grids are nested. The engine can perform fast block-aggregation (e.g., average $5 \times 5$ pixels).
- **keepinboth**: Used when you want to ensure the variable is available at both scales during cross-scale models.

## Creating a Custom Local Grid (Manual)

If you don't want to use the universal mesh (not recommended), you can register a `GridSpec` manually:

```python
from disscube.models import GridSpec

my_grid = GridSpec(
    id="ProjectX/30m",
    type="local",
    crs="EPSG:31983",
    resolution=30.0,
    bbox=[580000, 9700000, 600000, 9720000],
    description="Manual grid - won't align with BDC national mesh"
)
cube.register_grid(my_grid)
```
