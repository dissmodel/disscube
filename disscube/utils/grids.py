import math
from pyproj import Transformer
from disscube.models import GridSpec
from disscube.client import CubeClient

# ---------------------------------------------------------------------------
# Master Grid Constants (Brazil Data Cube Standard)
# ---------------------------------------------------------------------------

BDC_CRS = (
    "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22"
    " +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
)

# Full Brazil bbox in BDC Albers, snapped to 5 km mesh.
BRAZIL_BBOX = [2_720_000, 7_500_000, 7_870_000, 11_830_000]

# National reference resolutions
SIMULATION_GRIDS = [
    ("BR/5km",  5_000.0,  "National LUCC grid — 5 km pixels, BDC Albers"),
    ("BR/1km",  1_000.0,  "National LUCC grid — 1 km pixels, BDC Albers"),
]

# ---------------------------------------------------------------------------
# Grid Registration Utilities
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


def register_local_grid(
    cube: CubeClient,
    name: str | None = None,
    state: str | None = None,
    bbox_geo: tuple[float, float, float, float] | None = None,
    resolution: float = 5_000.0,
    snap: bool = True,
) -> GridSpec:
    """
    Register a local simulation grid snapped to the national mesh.
    
    This ensures that any Area of Interest (AOI) has pixels that align 
    perfectly with the national master grids, enabling interoperability 
    without resampling.
    """
    name = name or state
    if not name:
        raise ValueError("Either 'name' or 'state' must be provided.")
    
    if bbox_geo is None:
        raise ValueError("'bbox_geo' must be provided.")

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

    is_km = resolution >= 1000 and math.isclose(resolution % 1000, 0, abs_tol=1e-5)
    if is_km:
        res_str = f"{int(resolution // 1000)}km"
    else:
        res_str = f"{int(resolution)}m"

    grid_id = f"{name}/{res_str}"
    grid = GridSpec(
        id=grid_id,
        type="reference",
        crs=BDC_CRS,
        resolution=resolution,
        bbox=[minx, miny, maxx, maxy],
        description=f"{name} simulation grid — {resolution:.0f} m pixels, BDC Albers",
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
