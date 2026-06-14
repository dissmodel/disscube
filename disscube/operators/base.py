"""
Operator plugin registry for disscube.

Maps each operator name to its metadata: which requirements must be satisfied
at Derivation construction time (fail-fast validation before any I/O).
"""

from typing import TypedDict


class OperatorMeta(TypedDict):
    requires_class_code: bool


# Single source of truth for valid operator names and their constraints.
# The Aggregator (pipeline/aggregator.py) dispatches by the same names;
# adding an operator here AND in the Aggregator's dispatch block is the
# complete registration pattern.
OPERATOR_REGISTRY: dict[str, OperatorMeta] = {
    # ── Zonal operators (window-based aggregates over raster / vector data) ──
    "mean":       {"requires_class_code": False},
    "sum":        {"requires_class_code": False},
    "std":        {"requires_class_code": False},
    "min":        {"requires_class_code": False},
    "max":        {"requires_class_code": False},
    "majority":   {"requires_class_code": False},
    "minority":   {"requires_class_code": False},
    "percentage": {"requires_class_code": True},   # class_code selects the target class
    "attribute":  {"requires_class_code": False},
    "presence":   {"requires_class_code": False},
    # ── Proximity operators (distance / density to features) ─────────────────
    "min_distance": {"requires_class_code": False},
    "count":        {"requires_class_code": False},
}
