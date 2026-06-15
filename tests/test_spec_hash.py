"""
Tests for SpatialDerivation.spec_hash() determinism and correctness.

The spec_hash is the cache key for all derived outputs; any change to it
invalidates stored artefacts. Tests here guard against accidental changes
to hash composition.
"""

from disscube.models import SpatialDerivation, SpatialRelation, Variable


def _base():
    return SpatialDerivation(
        source_id="S1", grid_id="G1", role="driver",
        variables=[Variable(name="v", operator="mean")],
    )


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #

def test_spec_hash_is_deterministic():
    """Same derivation always produces the same hash across calls."""
    d = _base()
    assert d.spec_hash() == d.spec_hash()


def test_spec_hash_is_deterministic_across_instances():
    """Two independently constructed equal derivations share a hash."""
    assert _base().spec_hash() == _base().spec_hash()


# --------------------------------------------------------------------------- #
# Sensitivity to meaningful fields
# --------------------------------------------------------------------------- #

def test_different_source_ids_differ():
    d1 = _base()
    d2 = _base().model_copy(update={"source_id": "S2"})
    assert d1.spec_hash() != d2.spec_hash()


def test_different_grid_ids_differ():
    d1 = _base()
    d2 = _base().model_copy(update={"grid_id": "G2"})
    assert d1.spec_hash() != d2.spec_hash()


def test_different_roles_differ():
    d1 = _base()
    d2 = _base().model_copy(update={"role": "constraint"})
    assert d1.spec_hash() != d2.spec_hash()


def test_different_operators_differ():
    d1 = SpatialDerivation(source_id="S", grid_id="G", role="r",
                            variables=[Variable(name="v", operator="mean")])
    d2 = SpatialDerivation(source_id="S", grid_id="G", role="r",
                            variables=[Variable(name="v", operator="sum")])
    assert d1.spec_hash() != d2.spec_hash()


def test_different_valid_from_differ():
    d1 = _base().model_copy(update={"valid_from": "2020"})
    d2 = _base().model_copy(update={"valid_from": "2021"})
    assert d1.spec_hash() != d2.spec_hash()


def test_static_vs_temporal_differ():
    static = _base()
    temporal = _base().model_copy(update={"valid_from": "2020"})
    assert static.spec_hash() != temporal.spec_hash()


# --------------------------------------------------------------------------- #
# Insensitivity to SpatialRelation (correctness fix)
# --------------------------------------------------------------------------- #

def test_relations_do_not_affect_spec_hash():
    """
    Adding or changing SpatialRelation entries must NOT change the spec_hash.

    Relations are persisted in the catalog but no pipeline stage reads them
    during computation. Including them in the hash would make the cache key
    sensitive to documentation-level metadata, breaking the reproducibility
    guarantee: the same source + grid + operator + time window must always
    hash to the same key regardless of which relations are recorded.
    """
    without_relation = _base()
    with_relation = _base().model_copy(update={
        "relations": [
            SpatialRelation(source_grid_id="G1", target_grid_id="G2",
                            strategy="simple")
        ]
    })
    assert without_relation.spec_hash() == with_relation.spec_hash(), (
        "SpatialRelation must not affect spec_hash: relations are not used "
        "in the computation pipeline."
    )


def test_different_relations_produce_same_hash():
    """Two derivations that differ only in relations must hash identically."""
    r1 = _base().model_copy(update={
        "relations": [SpatialRelation(source_grid_id="A", target_grid_id="B",
                                      strategy="simple")]
    })
    r2 = _base().model_copy(update={
        "relations": [SpatialRelation(source_grid_id="X", target_grid_id="Y",
                                      strategy="chooseone")]
    })
    assert r1.spec_hash() == r2.spec_hash()
