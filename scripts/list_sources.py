from disscube.client import CubeClient

cube = CubeClient(catalog="catalog.db", store="./data/")

print("=== Registered Spatial Sources ===")
sources = cube.catalog.list_spatial_sources()

if not sources:
    print("No sources found in catalog.")
else:
    for src in sources:
        print(f"Source: {src.id}")
        print(f"  Name:   {src.name}")
        print(f"  Format: {src.format}")
        print(f"  URL:    {src.asset_url}")
        print(f"  CRS:    {src.crs}")
        if src.time:
            print(f"  Time:   {src.time}")
        print("-" * 30)
