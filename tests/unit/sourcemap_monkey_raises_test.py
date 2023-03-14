from contextlib import contextmanager

import pytest

from feature_gates import FeatureGates


@contextmanager
def sourcemap_disabled():
    previous = FeatureGates.sourcemap_enabled()
    FeatureGates.set_sourcemap_enabled(False)
    yield
    FeatureGates.set_sourcemap_enabled(previous)


@pytest.mark.serial
def test_sourcemap_fails_elegantly_when_disabled():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions
    from pyteal.errors import SourceMapDisabledError

    with sourcemap_disabled():
        with pytest.raises(
            SourceMapDisabledError, match="because stack frame discovery is turned off"
        ):
            router.compile(
                version=6,
                optimize=OptimizeOptions(scratch_slots=True),
                with_sourcemaps=True,
            )
