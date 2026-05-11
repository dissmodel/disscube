from disscube.client import CubeClient
from disscube.models import SpatialSource, SpatialDerivation, Variable
import os

def main():
    cube = CubeClient(catalog="catalog.json", store="./data/")
    
    # 1. Register Source
    ti_path = "zip://data/raw/terras_indigenas_funai_2010_limpo_poly_sirgas2000.zip"
    cube.register_spatial_source(SpatialSource(
        id="terras_indigenas",
        name="Terras Indígenas FUNAI 2010",
        format="vector",
        asset_url=ti_path,
        crs="EPSG:5880"
    ))
    print("Registered source: terras_indigenas")

    # 2. Derive Presence
    derivation = SpatialDerivation(
        source_id="terras_indigenas",
        grid_id="BR/5km",
        role="driver",
        variables=[
            Variable(name="presenca_ti", operator="presence")
        ]
    )

    print("Deriving presence map for Indigenous Lands...")
    cube.derive(derivation)
    print("Derivation successful.")

if __name__ == "__main__":
    main()
