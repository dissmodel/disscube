# DissCube Examples

This folder contains a structured demonstration of the DissCube pipeline, from catalog initialization to complete case studies.

## Execution Order

### 1. Setup (One-time)
Bootstrap the catalog and register baseline data.
- `python examples/setup/01_init_catalog.py`: Registers national and local simulation grids.
- `python examples/setup/02_register_sources.py`: Registers raw data files as SpatialSources.
- `python examples/setup/03_import_bdc_tiles.py`: Imports BDC tile definitions (one-time, slow).

### 2. National Drivers
Derive variables on the national 5 km mesh.
- `python examples/drivers/01_brazil_national.py`: Slope, TI presence, and distance to cities/rivers.

### 3. Case Study: Ilha do Maranhão
- `python examples/case_studies/ilha_maranhao/01_derive.py`: Temporal MapBiomas (majority) + static distance-to-seats variable.

### 4. Case Study: BR-MANGUE (Maranhão)
- `python examples/case_studies/brmangue/01_derive.py`: Derives land use and environmental variables at 100 m.
- `python examples/case_studies/brmangue/02_simulate.py`: Runs the BrmangueRasterExecutor.

### 5. Case Study: LUCC/AC (Acre)
- `python examples/drivers/02_acre_5km.py`: Derives Acre-specific drivers at 5 km.
- `python examples/case_studies/lucc_acre/01_derive.py`: Derives land use attributes from vector data.
- `python examples/case_studies/lucc_acre/02_simulate.py`: Runs the LUCCRasterExecutor.
- `python examples/case_studies/lucc_acre/03_temporal_drivers.py`: Simulation loop with temporal drivers.

---

**Utilitários:** `tools/zarr_to_tif.py` converte um arquivo Zarr derivado para GeoTIFF.
```
python tools/zarr_to_tif.py data/derived/.../var.zarr output.tif
```
