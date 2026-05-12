import unittest
from unittest.mock import MagicMock, patch
from disscube.client import CubeClient
from disscube.utils.bdc_importer import import_bdc_grids
import os
import json

class TestBDCMasterGrids(unittest.TestCase):
    def setUp(self):
        self.catalog_path = "test_catalog.json"
        self.store_path = "./test_store"
        if os.path.exists(self.catalog_path):
            os.remove(self.catalog_path)
        self.cube = CubeClient(self.catalog_path, self.store_path)

    def tearDown(self):
        if os.path.exists(self.catalog_path):
            os.remove(self.catalog_path)

    @patch('fiona.open')
    def test_importer_creates_3_grids(self, mock_fiona):
        # Mock fiona to return 2 tiles per size
        mock_src = MagicMock()
        mock_src.__enter__.return_value = [
            {'properties': {'tile': '001001'}, 'geometry': {'type': 'Polygon', 'coordinates': []}},
            {'properties': {'tile': '001002'}, 'geometry': {'type': 'Polygon', 'coordinates': []}}
        ]
        mock_fiona.return_value = mock_src

        import_bdc_grids(self.cube, "sm.shp", "md.shp", "lg.shp")

        # Verify 3 grids
        grids = self.cube.catalog.list_grids()
        grid_ids = [g.id for g in grids]
        self.assertIn("BDC_SM", grid_ids)
        self.assertIn("BDC_MD", grid_ids)
        self.assertIn("BDC_LG", grid_ids)
        self.assertEqual(len(grids), 3)

        # Verify sources
        sources = self.cube.catalog.list_spatial_sources()
        # 3 types * 2 tiles = 6 sources
        self.assertEqual(len(sources), 6)
        source_ids = [s.id for s in sources]
        self.assertIn("BDC_SM_001001", source_ids)
        self.assertIn("BDC_LG_001002", source_ids)

    @patch('disscube.pipeline.writer.VariableWriter._calculate_dir_hash')
    @patch('xarray.Dataset.to_zarr')
    @patch('fsspec.AbstractFileSystem.exists')
    def test_derive_uses_tile_id(self, mock_exists, mock_to_zarr, mock_hash):
        mock_exists.return_value = False
        mock_hash.return_value = "fake_hash"
        
        # Setup master grid and source
        from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable
        grid = GridSpec(id="BDC_SM", type="reference", crs="EPSG:31984", resolution=10, bbox=[0,0,100,100])
        source = SpatialSource(id="BDC_SM_001", name="Tile 001", format="raster", asset_url="tile.tif", crs="EPSG:31984")
        self.cube.register_grid(grid)
        self.cube.register_spatial_source(source)

        derivation = SpatialDerivation(
            source_id="BDC_SM_001",
            grid_id="BDC_SM",
            role="test",
            variables=[Variable(name="var1", operator="identity")]
        )

        from disscube.pipeline.writer import VariableWriter
        from disscube.pipeline.context import PipelineContext
        import xarray as xr
        import numpy as np

        writer = VariableWriter(self.cube.store, self.cube.catalog)
        
        ds = xr.Dataset({"var1": (("y", "x"), np.random.rand(10, 10))})
        ctx = PipelineContext(source=source, grid=grid, derivation=derivation, data=ds)
        
        writer.execute(ctx)

        # Check catalog
        derived = self.cube.catalog.search_derived_variables(grid_id="BDC_SM")
        self.assertEqual(len(derived), 1)
        self.assertEqual(derived[0].tile_id, "001")
        self.assertIn("001", derived[0].asset_url)
        self.assertIn("001", derived[0].id)

    @patch('xarray.open_zarr')
    def test_load_with_tile_id(self, mock_open_zarr):
        from disscube.models import DerivedVariable
        import xarray as xr
        
        # Setup mock DataArray
        mock_da = MagicMock(spec=xr.DataArray)
        mock_ds = MagicMock()
        mock_ds.__getitem__.return_value = mock_da
        mock_open_zarr.return_value = mock_ds
        
        # Setup 2 tiles for the same variable
        d1 = DerivedVariable(
            id="hash_001_var1", name="var1", grid_id="BDC_SM", role="test",
            times=[], dtype="float32", derivation_id="hash", spec_hash="hash",
            tile_id="001", asset_url="path/001.zarr"
        )
        d2 = DerivedVariable(
            id="hash_002_var1", name="var1", grid_id="BDC_SM", role="test",
            times=[], dtype="float32", derivation_id="hash", spec_hash="hash",
            tile_id="002", asset_url="path/002.zarr"
        )
        self.cube.catalog.save_derived(d1)
        self.cube.catalog.save_derived(d2)
        
        # Test 1: Load without tile_id when multiple exist -> should fail
        with self.assertRaises(ValueError) as cm:
            self.cube.load("var1")
        self.assertIn("Multiple tiles found", str(cm.exception))
        
        # Test 2: Load with specific tile_id -> should succeed
        res = self.cube.load("var1", tile_id="001")
        self.assertEqual(res, mock_da)
        mock_open_zarr.assert_called_with("path/001.zarr")

if __name__ == '__main__':
    unittest.main()
