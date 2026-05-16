# Pipeline Stages

The DisSCube pipeline is a sequence of idempotent stages. Each stage receives a `PipelineContext` and returns an updated one.

## 1. Normalizer
Handles the entry point of the data.
- **Vector**: Loads the shapefile/GPKG into a GeoDataFrame.
- **Raster**: Prepares lazy-loading parameters and validates coordinates.

## 2. GridAligner
The most critical spatial stage. It ensures the source data matches the `GridSpec` exactly.
- **Reprojection**: Uses `rioxarray` and `rasterio` to transform the source CRS to the target Grid CRS.
- **Resampling**: Applies the selected operator logic (Nearest, Bilinear, etc.) to match the grid resolution.
- **Cropping**: Clips the data to the grid's Bounding Box (BBOX).

## 3. Aggregator
Applies domain-specific logic (FillCell operators).
- **Proximity**: Calculates Euclidean distance transforms for vector features.
- **Zonal Stats**: Aggregates point or polygon data into grid cells.

## 4. VariableWriter
Persists the final result.
- **Format**: Saves as a Zarr dataset with consolidated metadata.
- **Hashing**: Calculates the `spec_hash` and `content_hash`.
- **Registration**: Updates the SQLite catalog with the new `DerivedVariable` entry.
