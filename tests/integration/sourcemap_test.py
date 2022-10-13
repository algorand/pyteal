import ast
from functools import reduce
import json
from pathlib import Path

from algosdk.source_map import R3SourceMap, R3SourceMapJSON

import pytest

from pyteal import OptimizeOptions
from pyteal.compiler.sourcemap import PyTealFrame, PyTealSourceMap, SourceMapItem
from pyteal.util import Frames

import pyteal as pt

from examples.application.abi.algobank import router

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"

FIXTURES = Path.cwd() / "tests" / "integration" / "sourcemaps"


def test_frames():
    this_file, this_func = "sourcemap_test.py", "test_frames"
    this_lineno, this_frame = 26, Frames()[1]
    code = f"    this_lineno, this_frame = {this_lineno}, Frames()[1]\n"
    this_col_offset, this_end_col_offset = 34, 42
    frame_info, node = this_frame.frame_info, this_frame.node

    assert frame_info.filename.endswith(this_file)
    assert this_func == frame_info.function
    assert frame_info.code_context
    assert len(frame_info.code_context) == 1
    assert code == frame_info.code_context[0]
    assert this_lineno == frame_info.lineno

    assert node
    assert this_lineno == node.lineno == node.end_lineno
    assert this_col_offset == node.col_offset
    assert this_end_col_offset == node.end_col_offset
    assert isinstance(node, ast.Call)
    assert isinstance(node.parent, ast.Subscript)  # type: ignore


"""
# TODO: Additional examples needed before merging:

1. Inline programs patched together from various sources
2. Example with OpUp
3. Run on the ABI Router example
4. Run on Steve's Staking Contract
5. Run an Ben's AMM

?. Beaker example

"""


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
    new_version = sourcemap._tabulate_for_dev()
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
    # TODO: add functionality that tallies the line statuses up and assert that all
    # statuses were > SourceMapItemStatus.PYTEAL_GENERATED

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


expr = pt.Int(0) + pt.Int(1)
expr_line_offset, expr_str = 128, "expr = pt.Int(0) + pt.Int(1)"


def test_SourceMapItem_source_mapping():
    def mock_teal(ops):
        return [f"{i+1}. {op}" for i, op in enumerate(ops)]

    ops = []
    b = expr.__teal__(pt.CompileOptions())[0]
    while b:
        ops.extend(b.ops)
        b = b.nextBlock  # type: ignore

    teals = mock_teal(ops)
    smis = [
        SourceMapItem(i + 1, teals[i], op, PyTealFrame(op.expr.frames[4]))
        for i, op in enumerate(ops)
    ]

    mock_source_lines = [""] * 500
    mock_source_lines[expr_line_offset] = expr_str
    source_files = ["sourcemap_test.py"]
    r3sm = R3SourceMap(
        file="dohhh.teal",
        source_root="~",
        entries={(i, 0): smi.source_mapping() for i, smi in enumerate(smis)},
        index=[(0,) for _ in range(3)],
        file_lines=list(map(lambda x: x.teal, smis)),
        source_files=source_files,
        source_files_lines=[mock_source_lines],
    )
    expected_json = '{"version": 3, "sources": ["tests/integration/sourcemap_test.py"], "names": [], "mappings": "AAgIA;AAAA;AAAA", "file": "dohhh.teal", "sourceRoot": "~"}'
    assert expected_json == json.dumps(r3sm.to_json())

    r3sm_unmarshalled = R3SourceMap.from_json(
        R3SourceMapJSON(**json.loads(expected_json)),
        sources_content_override=["\n".join(mock_source_lines)],
        target="\n".join(teals),
    )

    # TODO: test various properties of r3sm_unmarshalled

    assert expected_json == json.dumps(r3sm_unmarshalled.to_json())


def test_PyTealSourceMap_R3SourceMap_roundtrip():
    assert False, "test is currently RED"


def test_annotated_teal():
    compile_bundle = router.compile_program_with_sourcemaps(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
    )

    ptsm = compile_bundle.approval_sourcemap
    assert ptsm

    table = ptsm.annotated_teal()

    with open(FIXTURES / "algobank_annotated.teal", "w") as f:
        f.write(table)
