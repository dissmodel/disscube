from disscube.models import SpatialDerivation, Variable
import json
import hashlib

source_id = "slope_brazil"
grid_id = "BR/5km"

derivation = SpatialDerivation(
    source_id=source_id,
    grid_id=grid_id,
    role="driver",
    variables=[
        Variable(name="major_slope", operator="majority")
    ]
)

print(f"Spec Hash: {derivation.spec_hash()}")
