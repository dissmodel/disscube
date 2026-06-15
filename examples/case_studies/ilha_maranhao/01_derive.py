"""
examples/case_studies/ilha_maranhao/01_derive.py

Deriva variáveis para a Ilha do Maranhão usando MapBiomas:
  - uso (majority, temporal 2010-2022)
  - dist_sedes (min_distance, estática)

Pré-requisitos:
  - python examples/setup/01_init_catalog.py
  - python examples/setup/02_register_sources.py
  - Arquivos data/raw/ilha_maranhao_mapbiomas_{2010,2022}.tif presentes

Usage:
    python examples/case_studies/ilha_maranhao/01_derive.py
"""

from disscube.client import CubeClient
from disscube.models import SpatialSource, SpatialDerivation
from disscube.models.variable import Variable
from disscube.utils.grids import register_local_grid


def main():
    # ── 1. Cliente ───────────────────────────────────────────────────────────
    cube = CubeClient(catalog="catalog.db", store="data/")

    # ── 2. Grade local ───────────────────────────────────────────────────────
    register_local_grid(
        cube,
        name="ilha_maranhao",
        bbox_geo=(-44.42, -2.80, -44.02, -2.40),
        resolution=100,
        snap=True,
    )

    # ── 3. Derivação temporal (MapBiomas 2010, 2022) ─────────────────────────
    for year in [2010, 2022]:
        cube.register_spatial_source(SpatialSource(
            id=f"mapbiomas_ilha_ma_{year}",
            name=f"MapBiomas Ilha do Maranhão — {year}",
            format="raster",
            asset_url=f"data/raw/ilha_maranhao_mapbiomas_{year}.tif",
            crs="EPSG:4326",
            time=year,
        ))
        print(f"\n[pipeline] Processando ano {year}...")
        cube.derive(SpatialDerivation(
            source_id=f"mapbiomas_ilha_ma_{year}",
            grid_id="ilha_maranhao/100m",
            role="land_use",
            variables=[Variable(name="uso", operator="majority")],
        ))

    # ── 4. Variável estática ─────────────────────────────────────────────────
    print("\n[pipeline] Processando distância a sedes...")
    cube.derive(SpatialDerivation(
        source_id="urban_centers",
        grid_id="ilha_maranhao/100m",
        role="driver",
        variables=[Variable(name="dist_sedes", operator="min_distance")],
    ))

    # ── 5. Verificação ───────────────────────────────────────────────────────
    # "uso" retorna (time, y, x) por ser temporal; "dist_sedes" retorna (y, x)
    da_uso = cube.load("uso", grid_id="ilha_maranhao/100m")
    print(f"\nuso:       {da_uso.dims}  anos={list(da_uso.coords['time'].values)}")

    da_sedes = cube.load("dist_sedes", grid_id="ilha_maranhao/100m")
    print(f"dist_sedes:{da_sedes.dims}  shape={da_sedes.shape}")

    # ── 6. Integração DisSModel ──────────────────────────────────────────────
    backend = cube.to_lucc_data(["uso", "dist_sedes"], grid_id="ilha_maranhao/100m")
    print(f"\nBackend pronto: {backend}")


if __name__ == "__main__":
    main()
