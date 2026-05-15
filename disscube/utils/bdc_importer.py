from disscube.models import GridSpec, SpatialSource
from disscube.client import CubeClient
import fiona
from shapely.geometry import shape
import math

# ---------------------------------------------------------------------------
# BDC constants
# ---------------------------------------------------------------------------

BDC_CRS = (
    "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22"
    " +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
)

# Full Brazil bbox in BDC Albers, snapped to 5 km mesh.
# Derived from IBGE official limits (lon -73.99→-28.84, lat -33.75→5.27)
# reprojected to BDC Albers and aligned with floor/ceil to multiples of 5000 m.
# Produces 866 rows × 1030 cols at 5 km resolution (~892 k cells).
BRAZIL_BBOX = [2_720_000, 7_500_000, 7_870_000, 11_830_000]

# Simulation grids available for LUCC models.
# Resolution here is the TARGET pixel size of the derived product,
# NOT the native resolution of the satellite sensor inside each tile.
#
# BDC tile levels (SM / MD / LG) define spatial partitioning of scenes.
# They say nothing about what resolution a derived product should have.
SIMULATION_GRIDS = [
    # id        resolution (m)   description
    ("BR/5km",  5_000.0,  "National LUCC grid — 5 km pixels, BDC Albers"),
    ("BR/1km",  1_000.0,  "National LUCC grid — 1 km pixels, BDC Albers"),
    ("BR/100m",   100.0,  "National coastal/fine grid — 100 m pixels, BDC Albers"),
]

# BDC tile levels — purely spatial partitioning, no pixel resolution implied
BDC_TILE_LEVELS = [
    # label   shapefile arg   description
    ("SM",  "sm_path",  "BDC Small tile grid  (~1.5° × 1.5°)"),
    ("MD",  "md_path",  "BDC Medium tile grid (~3° × 3°)"),
    ("LG",  "lg_path",  "BDC Large tile grid  (~6° × 6°)"),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def import_bdc_grids(cube: CubeClient, sm_path: str, md_path: str, lg_path: str):
    """Import BDC tiles and simulation grids into the DissCube catalog.

    Two distinct concepts are registered here:

    1. **Simulation GridSpecs** (``BR/5km``, ``BR/1km``, ``BR/100m``) — define
       the pixel resolution of *derived products* (LUCC model outputs).  These
       are independent of any BDC tile level; the resolution refers to the
       output raster, not to a satellite sensor.

    2. **BDC tile SpatialSources** (``BDC_SM_001014``, …) — spatial envelopes
       that describe where raw satellite scenes are located.  They carry a bbox
       but no pixel resolution, because that is a property of the image inside
       the tile, not of the tile itself.

    Parameters
    ----------
    cube:
        Initialised :class:`~disscube.client.CubeClient`.
    sm_path, md_path, lg_path:
        Paths to the BDC SM / MD / LG shapefiles (``BDC_SM_V2.shp``, …).
    """
    register_simulation_grids(cube)
    paths = {"sm_path": sm_path, "md_path": md_path, "lg_path": lg_path}
    _register_tile_sources(cube, paths)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def register_simulation_grids(cube: CubeClient) -> None:
    """Register national simulation grids (pixel resolution of derived output)."""
    for grid_id, resolution, description in SIMULATION_GRIDS:
        grid = GridSpec(
            id=grid_id,
            type="reference",
            crs=BDC_CRS,
            resolution=resolution,
            bbox=BRAZIL_BBOX,
            description=description,
        )
        cube.register_grid(grid)
        print(f"  [grid] registered {grid_id!r}  ({resolution:.0f} m pixels, "
              f"{grid.rows} rows × {grid.cols} cols)")


def _register_tile_sources(cube: CubeClient, paths: dict[str, str]) -> None:
    """Register BDC tile envelopes as SpatialSources (no pixel resolution)."""
    level_paths = [
        ("SM", paths["sm_path"]),
        ("MD", paths["md_path"]),
        ("LG", paths["lg_path"]),
    ]
    for label, path in level_paths:
        print(f"\nImporting BDC_{label} tiles from {path} …")
        count = 0
        with fiona.open(path) as src:
            for rec in src:
                tile_id: str = rec["properties"]["tile"]
                geom = shape(rec["geometry"])
                bbox = list(geom.bounds)

                source = SpatialSource(
                    id=f"BDC_{label}_{tile_id}",
                    name=f"BDC {label} Tile {tile_id}",
                    format="raster",
                    # asset_url points to where the raw scene lives on disk / S3.
                    # The pixel resolution of that scene is internal to the file;
                    # it is NOT stored on SpatialSource.
                    asset_url=f"data/bdc/{label}/{tile_id}.tif",
                    crs=BDC_CRS,
                    bbox=bbox,
                )
                cube.register_spatial_source(source)
                count += 1

        print(f"  [tiles] registered {count} BDC_{label} tiles")


def register_state_grid(
    cube: CubeClient,
    state: str,
    bbox_geo: tuple[float, float, float, float],
    resolution: float = 5_000.0,
    snap: bool = True,
) -> GridSpec:
    """Register a state-level simulation grid snapped to the national 5 km mesh.

    Parameters
    ----------
    cube:
        Initialised :class:`~disscube.client.CubeClient`.
    state:
        Two-letter state abbreviation (e.g. ``"AC"``).
    bbox_geo:
        Geographic bounding box ``(lon_min, lat_min, lon_max, lat_max)``
        in EPSG:4326.
    resolution:
        Target pixel size in metres.  Defaults to 5 000 m.
    snap:
        If ``True`` (default), align bbox to the nearest multiple of
        *resolution* so that state grids are consistent with the national mesh.

    Returns
    -------
    GridSpec
        The registered grid.

    Example
    -------
    >>> grid = register_state_grid(
    ...     cube, "AC",
    ...     bbox_geo=(-74.0, -11.2, -66.5, -7.1),
    ...     resolution=5_000.0,
    ... )
    >>> print(grid.rows, grid.cols)
    102 169
    """
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", BDC_CRS, always_xy=True)

    corners = [
        (bbox_geo[0], bbox_geo[1]),  # SW
        (bbox_geo[0], bbox_geo[3]),  # NW
        (bbox_geo[2], bbox_geo[3]),  # NE
        (bbox_geo[2], bbox_geo[1]),  # SE
    ]
    xs, ys = zip(*(transformer.transform(lon, lat) for lon, lat in corners))

    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)

    if snap:
        minx = math.floor(minx / resolution) * resolution
        miny = math.floor(miny / resolution) * resolution
        maxx = math.ceil(maxx  / resolution) * resolution
        maxy = math.ceil(maxy  / resolution) * resolution

    grid_id = f"{state}/{resolution / 1000:.0f}km"
    grid = GridSpec(
        id=grid_id,
        type="reference",
        crs=BDC_CRS,
        resolution=resolution,
        bbox=[minx, miny, maxx, maxy],
        description=f"{state} simulation grid — {resolution:.0f} m pixels, BDC Albers",
    )
    cube.register_grid(grid)

    # Back-project for human-readable summary
    back = Transformer.from_crs(BDC_CRS, "EPSG:4326", always_xy=True)
    lon_min, lat_min = back.transform(minx, miny)
    lon_max, lat_max = back.transform(maxx, maxy)

    print(
        f"\n[grid] registered {grid_id!r}\n"
        f"  bbox (BDC Albers): [{minx:.0f}, {miny:.0f}, {maxx:.0f}, {maxy:.0f}]\n"
        f"  bbox (geographic): lon [{lon_min:.2f}, {lon_max:.2f}]  "
        f"lat [{lat_min:.2f}, {lat_max:.2f}]\n"
        f"  size: {grid.rows} rows × {grid.cols} cols = "
        f"{grid.rows * grid.cols:,} cells  ({resolution:.0f} m pixels)"
    )
    return grid


