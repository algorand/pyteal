from pathlib import Path

import pytest

RPS = Path.cwd() / "tests" / "teal"


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
def test_no_regression_with_sourcemap_as_configured_rps():
    no_regressions_rps()


@pytest.mark.serial
def test_no_regression_with_sourcemap_enabled_rps():
    from pyteal.stack_frame import NatalStackFrame

    originally = NatalStackFrame._no_stackframes
    NatalStackFrame._no_stackframes = False

    no_regressions_rps()

    NatalStackFrame._no_stackframes = originally


@pytest.mark.serial
def test_no_regression_with_sourcemap_disabled_rps():
    from pyteal.stack_frame import NatalStackFrame

    originally = NatalStackFrame._no_stackframes
    NatalStackFrame._no_stackframes = True

    no_regressions_rps()

    NatalStackFrame._no_stackframes = originally
