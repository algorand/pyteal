import pytest

from feature_gates import FeatureGates


@pytest.mark.serial
def test_feature_gates():
    with pytest.raises(ValueError, match="Unknown feature='foo'"):
        FeatureGates.get("foo")

    with pytest.raises(ValueError, match="Cannot set unknown feature='foo'"):
        FeatureGates.set("foo", 42)

    default_sourcemap_gate: bool = FeatureGates._gates.sourcemap_enabled
    default_sourcemap_debug_gate: bool = FeatureGates._gates.sourcemap_debug
    assert FeatureGates.get("sourcemap_enabled") is default_sourcemap_gate
    assert FeatureGates.get("sourcemap_debug") is default_sourcemap_debug_gate
    assert FeatureGates.sourcemap_enabled() is default_sourcemap_gate
    assert FeatureGates.sourcemap_debug() is default_sourcemap_debug_gate

    from pyteal import stack_frame

    assert stack_frame.NatalStackFrame.sourcemapping_is_off() is True

    # enable source mapping:
    FeatureGates.set("sourcemap_enabled", True)
    FeatureGates.set("sourcemap_debug", True)
    assert FeatureGates._gates.sourcemap_enabled is True
    assert FeatureGates._gates.sourcemap_debug is True
    assert FeatureGates.get("sourcemap_enabled") is True
    assert FeatureGates.get("sourcemap_debug") is True
    assert FeatureGates.sourcemap_enabled() is True
    assert FeatureGates.sourcemap_debug() is True

    assert stack_frame.NatalStackFrame.sourcemapping_is_off() is False

    # disable source mapping:
    FeatureGates.set("sourcemap_enabled", False)
    FeatureGates.set("sourcemap_debug", False)
    assert FeatureGates._gates.sourcemap_enabled is False
    assert FeatureGates._gates.sourcemap_debug is False
    assert FeatureGates.get("sourcemap_enabled") is False
    assert FeatureGates.get("sourcemap_debug") is False
    assert FeatureGates.sourcemap_enabled() is False
    assert FeatureGates.sourcemap_debug() is False
