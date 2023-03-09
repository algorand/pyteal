import pytest

from feature_gates import FeatureGates, _FeatureGatesConfig

# from pyteal.stack_frame import _sourcmapping_is_off


def test_feature_gates():
    with pytest.raises(ValueError, match="Unknown feature='foo'"):
        FeatureGates.get("foo")

    with pytest.raises(ValueError, match="Feature sourcemap_enabled is not set"):
        FeatureGates.get("sourcemap_enabled")

    with pytest.raises(ValueError, match="Feature sourcemap_enabled is not set"):
        FeatureGates.sourcemap_enabled()

    FeatureGates.set("sourcemap_enabled", True)
    assert FeatureGates.get("sourcemap_enabled") is True
    assert FeatureGates.sourcemap_enabled() is True

    with pytest.raises(ValueError, match="Feature sourcemap_debug is not set"):
        FeatureGates.get("sourcemap_debug")

    with pytest.raises(ValueError, match="Feature sourcemap_debug is not set"):
        FeatureGates.sourcemap_debug()

    FeatureGates.load()
    # `sourcemap_enabled` wasn't affected by loading:
    assert FeatureGates.get("sourcemap_enabled") is True
    assert FeatureGates.sourcemap_enabled() is True

    # but `sourcempa_debug` was affected:
    assert FeatureGates.get("sourcemap_debug") is False
    assert FeatureGates.sourcemap_debug() is False


def test_feature_gates_load():
    # before loading, the gates are empty
    all_empty = _FeatureGatesConfig(None, None)
    assert all_empty == FeatureGates._gates

    # sanity DEFAULTS check
    all_off = _FeatureGatesConfig(False, False)
    assert all_off == FeatureGates.DEFAULTS

    # load without a config file
    FeatureGates.load()
    assert FeatureGates.DEFAULTS == FeatureGates._gates

    # load with all-off config file
    FeatureGates.load(config_path="tests/unit/fixtures/all_off.ini", overwrite=True)
    assert all_off == FeatureGates._gates

    # load with all-on config file
    all_on = _FeatureGatesConfig(True, True)
    FeatureGates.load(config_path="tests/unit/fixtures/all_on.ini", overwrite=True)
    assert all_on == FeatureGates._gates

    # load with all-off config file, but without overwrite
    FeatureGates.load(config_path="tests/unit/fixtures/all_off.ini", overwrite=False)
    # nothing changed
    assert all_on == FeatureGates._gates

    # turn off sourcemap_debug
    assert FeatureGates.sourcemap_debug() is True
    FeatureGates.set_sourcemap_debug(False)
    assert FeatureGates.sourcemap_debug() is False

    # load with default (non-overwrite) config file
    FeatureGates.load(config_path="tests/unit/fixtures/all_on.ini")
    assert FeatureGates.sourcemap_debug() is False

    # load again, but with overwrite
    FeatureGates.load(config_path="tests/unit/fixtures/all_on.ini", overwrite=True)
    assert FeatureGates.sourcemap_debug() is True
