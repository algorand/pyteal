import json
from pathlib import Path

import pytest

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"
RPS = Path.cwd() / "tests" / "teal"


def compare_and_assert(file, actual):
    with open(file, "r") as f:
        expected_lines = f.read().splitlines()
        actual_lines = actual.splitlines()
        assert len(expected_lines) == len(actual_lines)
        assert expected_lines == actual_lines


def no_regressions_algobank():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    approval, clear, contract = router.compile_program(
        version=6, optimize=OptimizeOptions(scratch_slots=True)
    )

    compare_and_assert(
        ALGOBANK / "algobank.json", json.dumps(contract.dictify(), indent=4)
    )
    compare_and_assert(ALGOBANK / "algobank_clear_state.teal", clear)
    compare_and_assert(ALGOBANK / "algobank_approval.teal", approval)


@pytest.mark.serial
def test_no_regression_with_sourcemap_as_configured_algobank():
    no_regressions_algobank()


def no_regressions_rps():
    from pyteal import compileTeal, Mode
    from tests.teal.rps import approval_program

    compiled = compileTeal(approval_program(), Mode.Application, version=6)
    compare_and_assert(RPS / "rps.teal", compiled)


@pytest.mark.serial
def test_no_regressions_with_sourcemap_as_configured_rps():
    no_regressions_rps()
