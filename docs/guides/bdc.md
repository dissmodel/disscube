# Brazil Data Cube Integration

DisSCube provides first-class support for the **Brazil Data Cube (BDC)** hierarchical grid system.

## Master Grids vs. Tiles

The BDC partitions Brazil into tiles. In DisSCube, we represent this using **Master Grids** (the resolution definition) and **Spatial Sources** (the individual tiles).

### Available Master Grids
- `BDC_SM`: 10m resolution (Small tiles).
- `BDC_MD`: 30m resolution (Medium tiles).
- `BDC_LG`: 60m resolution (Large tiles).
- `BDC_100m`: 100m custom resolution (Continental scale).

## Tiled Derivation

When you run a derivation, you specify the `tile_id`. DisSCube performs the following steps:

1. **Lookup**: Finds the BBOX of the tile in the catalog.
2. **Crop**: Restricts the Master Grid to that specific BBOX.
3. **Process**: Executes the operators only for that area.
4. **Partition**: Saves the Zarr file in a directory named after the tile.

This approach allows you to process a single tile for testing or iterate through all tiles of Brazil using a simple loop, without ever hitting memory limits.

```python
# Processing multiple tiles in a loop
for tile in ["008013", "008014", "008015"]:
    cube.derive(my_derivation, tile_id=tile)
```
