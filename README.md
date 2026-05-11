# DisSCube

> **⚠️ Project Status: Early Stage (Alpha)**
> This project is currently in its initial development phase. APIs and data structures are subject to frequent changes as we evolve the core engine. Contributions and feedback are welcome!

DisSCube is a high-performance spatial data cube engine designed for land change modeling within the **DisSModel** ecosystem. It provides a bridge between raw geospatial data (Rasters, Vectors, Points) and multidimensional analysis ready for statistical and dynamic models (like TerraME).

## 🚀 Key Features

- **FillCell Inspired Operators**: Implements the legacy logic of the TerraView FillCell plugin for robust data aggregation.
    - **Raster**: Majority (Mode), Mean, Max, Min, and Sum resampling.
    - **Vector**: Presence (Boolean), Count, and area-weighted strategies.
    - **Proximity**: High-performance Euclidean distance transforms.
- **Hierarchical Grid Management**: Native support for **Brazil Data Cube (BDC)** grids (SM, MD, LG) and custom local grids.
- **Multidimensional Storage**: Uses **Zarr** and **Xarray** for efficient storage and retrieval of high-resolution spatial variables.
- **GIS Integration**: Built-in tools for exporting cube slices to GeoTIFF for validation in QGIS.

## 🛠 Architecture

DisSCube operates on a **Research -> Strategy -> Execution** lifecycle:
1. **Catalog**: A JSON-based registry for Grids, Spatial Sources, and Derived Variables.
2. **Pipeline**: A series of stages (Normalize -> Align -> Aggregate -> Write) that transform raw data into aligned cube variables.
3. **Storage**: An abstraction layer for local or cloud-based Zarr assets.

## 📖 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dissmodel/disscube.git
cd disscube

# Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Basic Usage

```python
from disscube.client import CubeClient
from disscube.models import Variable, SpatialDerivation

# Initialize client
cube = CubeClient(catalog="catalog.json", store="./data/")

# Define a derivation (e.g., Majority Slope at 5km)
derivation = SpatialDerivation(
    source_id="slope_brazil",
    grid_id="BR/5km",
    role="driver",
    variables=[
        Variable(name="major_slope", operator="majority")
    ]
)

# Execute pipeline
cube.derive(derivation)

# Load data as Xarray
da = cube.load("major_slope")
```

## 🔍 Tools

The project includes specialized tools for data verification:
- `zarr_to_tif.py`: Export any derived variable from the cube to a georeferenced GeoTIFF.
  ```bash
  python tools/zarr_to_tif.py BR/5km major_slope
  ```

## 🗺 Roadmap

- [x] Brazil-scale 5km grid support.
- [x] Native FillCell operators (Presence, Majority, Mean).
- [ ] Area-Weighted Sum for population volume preservation.
- [ ] Dask integration for parallel processing of continental datasets.
- [ ] Direct integration with `dissmodel-platform`.

## 📄 License

This project is part of the DisSModel ecosystem. See the LICENSE file for details.
