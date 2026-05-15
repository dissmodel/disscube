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

# Full Brazil bbox in BDC Albers (used only as spatial envelope for tile grids)
BRAZIL_BBOX = [2_400_000, 7_100_000, 8_200_000, 12_100_000]

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
    """Register BDC tile envelopes as SpatialSources in the DissCube catalog.

    This function registers **only** BDC tile spatial envelopes
    (``BDC_SM_001014``, …).  Each tile is a geographic container for raw
    satellite scenes; it carries a bbox but no pixel resolution, because
    that is a property of the image inside the tile, not of the tile itself.

    Simulation GridSpecs (``BR/5km``, ``BR/1km``, ``BR/100m``) are
    intentionally **not** registered here — they are owned by the catalog
    setup script (``01_setup_catalog.py``) to avoid duplicate registration.
    Call :func:`register_simulation_grids` directly if you need them
    standalone.

    Parameters
    ----------
    cube:
        Initialised :class:`~disscube.client.CubeClient`.
    sm_path, md_path, lg_path:
        Paths to the BDC SM / MD / LG shapefiles (``BDC_SM_V2.shp``, …).
    """
    paths = {"sm_path": sm_path, "md_path": md_path, "lg_path": lg_path}
    _register_tile_sources(cube, paths)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def register_simulation_grids(cube: CubeClient) -> None:
    """Register national simulation grids into the DissCube catalog.

    Registers ``BR/5km``, ``BR/1km``, and ``BR/100m`` GridSpecs covering
    all of Brazil in BDC Albers.  The ``resolution`` field is the pixel
    size of the *derived product* (LUCC model output) — completely
    independent of the native sensor resolution inside any BDC tile.

    Call this once from the catalog setup script.  Do **not** call from
    :func:`import_bdc_grids` to avoid duplicate registration.
    """
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cube = CubeClient(catalog="catalog.db", store="./data/")

    import_bdc_grids(
        cube,
        sm_path="/tmp/bdc_grids/SM/BDC_SM_V2.shp",
        md_path="/tmp/bdc_grids/MD/BDC_MD_V2.shp",
        lg_path="/tmp/bdc_grids/LG/BDC_LG_V2.shp",
    )

    # Register Acre at 5 km — snapped to national mesh
    register_state_grid(
        cube,
        state="AC",
        bbox_geo=(-74.0, -11.2, -66.5, -7.1),
        resolution=5_000.0,
    )