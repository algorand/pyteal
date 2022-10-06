from pathlib import Path
import json

from pyteal import OptimizeOptions

from examples.application.abi.algobank import router

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"


def test_no_regression():
    approval, clear, contract = router.compile_program(
        version=6, optimize=OptimizeOptions(scratch_slots=True)
    )

    with open(ALGOBANK / "algobank_approval.teal") as af:
        assert approval == af.read()

    with open(ALGOBANK / "algobank_clear_state.teal") as cf:
        assert clear == cf.read()

    with open(ALGOBANK / "algobank.json") as jf:
        assert json.dumps(contract.dictify(), indent=4) == jf.read()


def test_sourcemaps():
    compile_bundle = router.compile_program_with_sourcemaps(
        version=6, assemble_constants=True, optimize=OptimizeOptions(scratch_slots=True)
    )

    x = 42
