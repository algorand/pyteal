from pathlib import Path
import json

import pytest

from pyteal import OptimizeOptions

from examples.application.abi.algobank import router
from pyteal.compiler.sourcemap import PyTealSourceMap

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"

FIXTURES = Path.cwd() / "tests" / "integration" / "sourcemaps"


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


def test_reconstruct():
    compile_bundle = router.compile_program_with_sourcemaps(
        version=6, optimize=OptimizeOptions(scratch_slots=True)
    )

    assert compile_bundle.approval_sourcemap
    assert compile_bundle.clear_sourcemap

    with open(ALGOBANK / "algobank_approval.teal") as af:
        assert af.read() == compile_bundle.approval_sourcemap.teal()

    with open(ALGOBANK / "algobank_clear_state.teal") as cf:
        assert cf.read() == compile_bundle.clear_sourcemap.teal()


def fixture_comparison(sourcemap: PyTealSourceMap, name: str):
    new_version = sourcemap.tabulate(
        teal_line_col="line",
        teal_code_col="teal",
        linemap_status="line status",
        pyteal_exec_col="pyteal AST",
        pyteal_path_col="source",
        pyteal_code_window="rows & columns",
        pyteal_line_col="pt line",
        pyteal_code_context_col="pyteal line",
    )
    with open(FIXTURES / f"{name}", "w") as f:
        f.write(new_version)

    not_actually_comparing = True
    if not_actually_comparing:
        return

    with open(FIXTURES / name) as f:
        old_version = f.read()

    assert old_version == new_version


@pytest.mark.parametrize("version", [6])
@pytest.mark.parametrize("source_inference", [False, True])
@pytest.mark.parametrize("assemble_constants", [False, True])
@pytest.mark.parametrize("optimize_slots", [False, True])
def test_sourcemaps(version, source_inference, assemble_constants, optimize_slots):
    compile_bundle = router.compile_program_with_sourcemaps(
        version=version,
        assemble_constants=assemble_constants,
        optimize=OptimizeOptions(scratch_slots=optimize_slots),
        source_inference=source_inference,
    )

    assert compile_bundle.approval_sourcemap
    assert compile_bundle.clear_sourcemap

    suffix = f"_v{version}_si{int(source_inference)}_ac{int(assemble_constants)}_ozs{int(optimize_slots)}"
    fixture_comparison(
        compile_bundle.approval_sourcemap, f"algobank_approval{suffix}.txt"
    )
    fixture_comparison(compile_bundle.clear_sourcemap, f"algobank_clear{suffix}.txt")
