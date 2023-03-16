from pathlib import Path
import pytest

from feature_gates import FeatureGates

RPS = Path.cwd() / "tests" / "teal"


@pytest.fixture
def sourcemap_enabled():
    previous = FeatureGates.sourcemap_enabled()
    FeatureGates.set_sourcemap_enabled(True)
    yield
    FeatureGates.set_sourcemap_enabled(previous)


@pytest.fixture
def sourcemap_disabled():
    previous = FeatureGates.sourcemap_enabled()
    FeatureGates.set_sourcemap_enabled(False)
    yield
    FeatureGates.set_sourcemap_enabled(previous)


def compare_and_assert(file, actual):
    with open(file, "r") as f:
        expected_lines = f.read().splitlines()
        actual_lines = actual.splitlines()
        assert len(expected_lines) == len(actual_lines)
        assert expected_lines == actual_lines


def no_regressions_rps():
    from pyteal import compileTeal, Mode
    from tests.teal.rps import approval_program

    compiled = compileTeal(approval_program(), Mode.Application, version=6)
    compare_and_assert(RPS / "rps.teal", compiled)


@pytest.mark.serial
def test_annotated_rps(sourcemap_enabled):
    from pyteal import Compilation, Mode
    from pyteal.compiler.sourcemap import _PyTealSourceMapper
    from tests.teal.rps import approval_program

    with open(RPS / "rps.teal", "r") as f:
        expected_teal = f.read()

    with open(RPS / "rps_annotated.teal", "r") as f:
        expected_annotated = f.read()

    cbundle = Compilation(approval_program(), Mode.Application, version=6).compile(
        with_sourcemap=True,
        annotate_teal=True,
        annotate_teal_headers=True,
        annotate_teal_concise=False,
    )
    teal, annotated = cbundle.teal, cbundle.sourcemap.annotated_teal

    assert expected_teal == teal
    assert expected_annotated == annotated
    _PyTealSourceMapper._validate_annotated(
        False, teal.splitlines(), annotated.splitlines()
    )


@pytest.mark.serial
def test_no_regression_with_sourcemap_as_configured_rps():
    no_regressions_rps()


@pytest.mark.serial
def test_no_regression_with_sourcemap_enabled_rps(sourcemap_enabled):
    from pyteal.stack_frame import NatalStackFrame

    assert NatalStackFrame.sourcemapping_is_off() is False

    no_regressions_rps()


@pytest.mark.serial
def test_no_regression_with_sourcemap_disabled_rps(sourcemap_disabled):
    from pyteal.stack_frame import NatalStackFrame

    assert NatalStackFrame.sourcemapping_is_off()

    no_regressions_rps()
