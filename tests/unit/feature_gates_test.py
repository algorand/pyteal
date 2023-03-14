import pytest

from feature_gates import FeatureGates


@pytest.mark.serial
def test_feature_gates():
    with pytest.raises(ValueError, match="Unknown feature='foo'"):
        FeatureGates.get("foo")

    with pytest.raises(ValueError, match="Cannot set unknown feature='foo'"):
        FeatureGates.set("foo", 42)

    # presently, source mapping features are off by default:
    assert FeatureGates.get("sourcemap_enabled") is False
    assert FeatureGates.get("sourcemap_debug") is False
    assert FeatureGates.sourcemap_enabled() is False
    assert FeatureGates.sourcemap_debug() is False

    from pyteal import stack_frame

    assert stack_frame.NatalStackFrame.sourcemapping_is_off() is True

    # enable source mapping:
    FeatureGates.set("sourcemap_enabled", True)
    FeatureGates.set("sourcemap_debug", True)
    assert FeatureGates.get("sourcemap_enabled") is True
    assert FeatureGates.get("sourcemap_debug") is True
    assert FeatureGates.sourcemap_enabled() is True
    assert FeatureGates.sourcemap_debug() is True

    # unfortunately, it's too late to enable source mapping:
    assert stack_frame.NatalStackFrame.sourcemapping_is_off() is True

    # but if we reload now...
    import importlib

    importlib.reload(stack_frame)

    assert stack_frame.NatalStackFrame.sourcemapping_is_off() is False
