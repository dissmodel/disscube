# From TerraME *Fill Cells* to DisSCube operators

## Lineage

DisSCube's derivation layer is the conceptual successor of TerraME's
`fillCellularSpace` (the *Fill Cells* operation), reformulated as a
reproducible, catalogued data-cube layer.

In TerraME/LuccME, populating a cellular space with attributes derived from
heterogeneous geographic layers is performed cell by cell, in Lua, through
fill *strategies* (`area`, `presence`, `count`, `distance`, `percentage`,
`majority`, `average`, etc.). DisSCube keeps the same semantic vocabulary but
expresses each strategy as a typed, auto-registered `Operator` that runs over a
catalogued data cube rather than over an in-memory cellular space.

The advance is not the set of operations — those are deliberately faithful to
TerraME — but the engineering around them:

- **Reproducibility.** Every derived product carries a deterministic
  `spec_hash`; identical specifications always produce the same catalogued
  product.
- **Grid-aligned aggregation.** Categorical and standard-deviation operators
  aggregate from a fine array snapped to the target grid origin, using real
  per-cell windows, so target resolutions that are not integer multiples of the
  source (e.g. 30 m → 1000 m) are well defined rather than silently
  approximated.
- **Explicit cell purity.** Coverage purity (valid / total pixels) and, for
  categorical operators, dominance purity (dominant-class fraction) are computed
  per cell. They are first-class metadata travelling with the variable, ready
  for a future masking policy. Purity is implicit in TerraME; here it is named
  and measurable — matching the parameter the INPE e-Cube design also elevates.
- **CRS robustness.** Aggregation is validated on real projected CRSs,
  including the BDC Brazil Albers grid, with named-WKT serialization to avoid
  `PROJCS["unknown"]` round-trip problems.

## Strategy → operator correspondence

| TerraME fill strategy | DisSCube operator (`name`) | Status | Notes |
|---|---|---|---|
| `presence` | `presence` | implemented | Binary mask: 1 where any feature is present. |
| `area` / `coverage` / `percentage` | `percentage` | implemented (window-based) | Fraction (0..1) of the target class per cell, over valid pixels. Requires `class_code`. |
| `majority` / `mode` | `majority` | implemented (window-based) | Dominant class per cell; ties resolve to the smallest class value. |
| `minority` | `minority` | implemented (window-based) | Least-frequent class per cell. |
| `count` | `count` | implemented | Count of features per cell (proximity operator). |
| `distance` | `min_distance` | implemented | Euclidean distance to the nearest feature (EDT × resolution). |
| `average` / `mean` | `mean` | implemented | Mean value per cell (continuous). |
| `sum` | `sum` | implemented | Sum per cell (continuous). |
| `minimum` | `min` | implemented | Minimum per cell. |
| `maximum` | `max` | implemented | Maximum per cell. |
| `stdev` / `standardDeviation` | `std` | implemented (window-based) | True per-cell standard deviation over valid pixels. |
| `attribute` (value copy) | `attribute` | implemented (vector) | Rasterize a numeric vector column whose name matches the variable. |

## Aggregation path by operator type

- **Continuous, resampling-expressible** (`mean`, `sum`, `min`, `max`): aligned
  to the target grid directly via the corresponding rasterio resampling method.
- **Categorical** (`percentage`, `majority`, `minority`) and **`std`**: aligned
  to a fine, origin-snapped grid with nearest resampling (never averaging a
  class code), then reduced per target cell over real windows. These operators
  set `needs_fine_alignment = True`.
- **Vector** (`presence`, `attribute`, and the vector branch of the categorical
  operators): reprojected and clipped to the grid bounding box, then rasterized.

## Known gaps relative to TerraME

- **Area-weighted vector aggregation.** For vector sources, fractional-coverage
  strategies are currently rasterized rather than area-weighted; the
  raster-fine path is the recommended route for fractional drivers. Area-weighted
  vector aggregation remains future work.
- **In-memory, single-tile by design.** The fine-alignment path materializes a
  fine array in memory; very large tiles at a high fine/target ratio are bounded
  by available memory. Distributed/lazy execution is a roadmap item, not a
  current capability.

## Positioning statement

> The filling of cellular spaces from heterogeneous geographic data — the core
> operation of TerraME's `fillCellularSpace` — is reformulated in DisSCube as a
> reproducible spatial-derivation layer: fill strategies become typed operators
> over a catalogued data cube, with aggregation on windows aligned to the target
> grid and explicit control of cell purity.
