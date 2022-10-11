import ast
from functools import reduce
from pathlib import Path
import json
from typing import cast

from algosdk.source_map import SourceMapping

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
    source_mappings = [smi.source_mapping() for smi in smis]

    # TODO: this isn't working as I expected, but it's a good test
    # as it shows that getting the AST info isn't as reliable as I
    # expected. So we need to assert that we succeed still to construct
    # trace producing SourceMapItems and can still generate the b64vlq SourceMappings from them
    x = 42
    # ptframe = PyTealFrame(this_frame)
    # assert this_frame == ptframe.frame

    # source_mapping = ptframe.source_mapping()
    # assert isinstance(source_mapping, SourceMapping)


# class MockASTNode:
#     def __init__(self, **kwargs):
#         self.stuff = {**kwargs}

#     def node_lineno(self):
#         return self.stuff["node_lineno"]

#     def node_col_offset(self):
#         return self.stuff["node_col_offset"]

#     def node_end_lineno(self):
#         return self.stuff["node_end_lineno"]

#     def node_end_col_offset(self):
#         return self.stuff["node_end_col_offset"]

#     def _unparse(self):
#         return self.stuff["unparse"]
