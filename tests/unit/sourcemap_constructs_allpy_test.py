from feature_gates import FeatureGates

import pytest

from tests.unit.sourcemap_constructs311_test import (
    CONSTRUCTS,
    CONSTRUCTS_LATEST_VERSION,
    constructs_test,
)


@pytest.fixture
def sourcemap_enabled():
    previous = FeatureGates.sourcemap_enabled()
    FeatureGates.set_sourcemap_enabled(True)
    yield
    FeatureGates.set_sourcemap_enabled(previous)


@pytest.mark.slow
@pytest.mark.serial
@pytest.mark.parametrize("i, test_case", enumerate(CONSTRUCTS))
@pytest.mark.parametrize("mode", ["Application", "Signature"])
@pytest.mark.parametrize("version", range(2, CONSTRUCTS_LATEST_VERSION + 1))
def test_constructs_very_slow(sourcemap_enabled, i, test_case, mode, version):
    constructs_test(i, test_case, mode, version)
