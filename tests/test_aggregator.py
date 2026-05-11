import pytest
import xarray as xr
import numpy as np
from disscube.pipeline import PipelineContext
from disscube.pipeline.aggregator import Aggregator
from disscube.models import GridSpec, SpatialSource, SpatialDerivation, Variable

def test_aggregator_strict_bands():
    grid = GridSpec(id="G1", type="local", crs="EPSG:31982", resolution=10, bbox=[0,0,100,100])
    source = SpatialSource(
        id="S1", name="S1", format="raster", asset_url="test.tif", crs="EPSG:31982"
    )
    derivation = SpatialDerivation(
        source_id="S1", grid_id="G1", role="test",
        variables=[Variable(name="B1", operator="mean")]
    )
    
    # 2-band data
    data = xr.DataArray(
        np.zeros((2, 10, 10)),
        dims=("band", "y", "x"),
        coords={"band": [1, 2], "y": grid.ys, "x": grid.xs}
    )
    
    ctx = PipelineContext(source=source, grid=grid, derivation=derivation, data=data)
    agg = Aggregator()
    
    # 1 variable, will get band index 0. Should pass.
    agg.execute(ctx) 
    
    # Reset data for second test run
    ctx.data = data
    
    # Now try to get a variable at index 2 (doesn't exist)
    derivation.variables = [Variable(name="B1", operator="mean"), Variable(name="B2", operator="mean"), Variable(name="B3", operator="mean")]
    with pytest.raises(ValueError, match="No band available for variable 'B3' at index 2"):
        agg.execute(ctx)

def test_aggregator_band_map_out_of_range():
    grid = GridSpec(id="G1", type="local", crs="EPSG:31982", resolution=10, bbox=[0,0,100,100])
    # band_map points to band 3, but data only has 2
    source = SpatialSource(
        id="S1", name="S1", format="raster", asset_url="test.tif", crs="EPSG:31982",
        band_map={"B1": 3}
    )
    derivation = SpatialDerivation(
        source_id="S1", grid_id="G1", role="test",
        variables=[Variable(name="B1", operator="mean")]
    )
    
    data = xr.DataArray(
        np.zeros((2, 10, 10)),
        dims=("band", "y", "x"),
        coords={"band": [1, 2], "y": grid.ys, "x": grid.xs}
    )
    
    ctx = PipelineContext(source=source, grid=grid, derivation=derivation, data=data)
    agg = Aggregator()
    
    with pytest.raises(ValueError, match="Band index 3 for variable 'B1' is out of range"):
        agg.execute(ctx)
