"""
This file monkey-patches ConfigParser in order to enable
source mapping and test the results of source mapping various 
PyTeal apps.
"""

import ast
from configparser import ConfigParser
from ensurepip import version
from pathlib import Path
from tabnanny import verbose
from typing import cast

import pytest
from unittest import mock

from algosdk.source_map import R3SourceMap
from pyteal.compiler import sourcemap

from pyteal.compiler.compiler import Compilation
from pyteal.ir.ops import Mode


ALGOBANK = Path.cwd() / "examples" / "application" / "abi"

FIXTURES = Path.cwd() / "tests" / "unit" / "sourcemaps"


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_reconstruct(_):
    from pyteal import OptimizeOptions
    from examples.application.abi.algobank import router

    compile_bundle = router.compile_program_with_sourcemaps(
        version=6, optimize=OptimizeOptions(scratch_slots=True)
    )

    assert compile_bundle.approval_sourcemap
    assert compile_bundle.clear_sourcemap

    with open(ALGOBANK / "algobank_approval.teal") as af:
        assert af.read() == compile_bundle.approval_sourcemap.teal()

    with open(ALGOBANK / "algobank_clear_state.teal") as cf:
        assert cf.read() == compile_bundle.clear_sourcemap.teal()


def fixture_comparison(sourcemap: "PyTealSourceMap", name: str):
    new_version = sourcemap._tabulate_for_dev()
    with open(FIXTURES / f"_{name}", "w") as f:
        f.write(new_version)

    not_actually_comparing = False
    if not_actually_comparing:
        return

    with open(FIXTURES / name) as f:
        old_version = f.read()

    assert old_version == new_version


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
@pytest.mark.parametrize("version", [6])
@pytest.mark.parametrize("source_inference", [False, True])
@pytest.mark.parametrize("assemble_constants", [False, True])
@pytest.mark.parametrize("optimize_slots", [False, True])
def test_sourcemaps(_, version, source_inference, assemble_constants, optimize_slots):
    from pyteal import OptimizeOptions

    from examples.application.abi.algobank import router

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


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_annotated_teal(_):
    from pyteal import OptimizeOptions

    from examples.application.abi.algobank import router

    compile_bundle = router.compile_program_with_sourcemaps(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
    )

    ptsm = compile_bundle.approval_sourcemap
    assert ptsm

    table = ptsm.annotated_teal()

    with open(FIXTURES / "algobank_annotated.teal", "w") as f:
        f.write(table)

    table_ast = ptsm.annotated_teal(unparse_hybrid=True)

    with open(FIXTURES / "algobank_hybrid.teal", "w") as f:
        f.write(table_ast)

    table_concise = ptsm.annotated_teal(unparse_hybrid=True, concise=True)

    with open(FIXTURES / "algobank_concise.teal", "w") as f:
        f.write(table_concise)


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_mocked_config_for_frames(_):
    config = ConfigParser()
    assert config.getboolean("pyteal-source-mapper", "enabled") is True
    from pyteal.util import Frames

    assert Frames.skipping_all() is False
    assert Frames.skipping_all(_force_refresh=True) is False


# TODO: this is temporary


def make(x, y, z):
    import pyteal as pt

    return pt.Int(x) + pt.Int(y) + pt.Int(z)


import pyteal as pt

e1 = pt.Seq(pt.Pop(make(1, 2, 3)), pt.Pop(make(4, 5, 6)), make(7, 8, 9))


@pt.Subroutine(pt.TealType.uint64)
def foo(x):
    return pt.Seq(pt.Pop(e1), e1)


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_lots_o_indirection(_):
    bundle = pt.Compilation(foo(pt.Int(42)), pt.Mode.Application, version=6).compile(
        with_sourcemap=True
    )


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_r3sourcemap(_):
    from pyteal import OptimizeOptions

    from examples.application.abi.algobank import router

    file = "dummy filename"
    compile_bundle = router.compile_program_with_sourcemaps(
        version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=file
    )

    ptsm = compile_bundle.approval_sourcemap
    assert ptsm

    r3sm = ptsm.get_r3sourcemap()
    assert file == r3sm.file
    assert cast(str, r3sm.source_root).endswith("/pyteal/")
    assert list(range(len(r3sm.entries))) == [l for l, _ in r3sm.entries]
    assert all(c == 0 for _, c in r3sm.entries)
    assert all(x == (0,) for x in r3sm.index)
    assert len(r3sm.entries) == len(r3sm.index)

    source_files = [
        "examples/application/abi/algobank.py",
        "tests/unit/sourcemap_monkey_enabled_test.py",
    ]
    assert source_files == r3sm.source_files

    r3sm_json = r3sm.to_json()

    assert (
        "AAgBS;AAAA;AAAA;AAAA;AC8IT;ADpHA;AAAA;AAAA;ACoHA;AD5FA;AAAA;AAAA;AC4FA;AD/EA;AAAA;AAAA;AC+EA;AAAA;AAAA;AD/EA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AC+EA;AAAA;AD/EA;AAAA;AAAA;AC+EA;AD5FA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AC4FA;AAAA;AAAA;AAAA;AAAA;AD5FA;AAAA;AC4FA;ADpHA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACoHA;AAAA;ADpHA;AAAA;AAAA;ACoHA;AD9IS;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAJL;AACc;AAAd;AAA4C;AAAc;AAA3B;AAA/B;AAFuB;AAKlB;AAAA;AC8IT;ADxIuC;AAAA;ACwIvC;AD9IS;AAAA;AAAA;AAAA;AAI6B;AAAA;AC0ItC;AAAA;AAAA;ADvJkB;AAAgB;AAAhB;AAAP;ACuJX;AAAA;AAAA;AAAA;AAAA;AAAA;ADvGe;AAAA;AAA0B;AAAA;AAA1B;AAAP;AACO;AAAA;AAA4B;AAA5B;AAAP;AAEI;AAAA;AACA;AACa;AAAA;AAAkB;AAA/B;AAAmD;AAAA;AAAnD;AAHJ;ACqGR;AAAA;AAAA;AAAA;ADnFmC;AAAgB;AAA7B;ACmFtB;AAAA;AAAA;AAAA;AAAA;AAAA;AD3DY;AACA;AACa;AAAc;AAA3B;AAA+C;AAA/C;AAHJ;AAKA;AACA;AAAA;AAG2B;AAAA;AAH3B;AAIyB;AAJzB;AAKsB;AALtB;AAQA;AAAA"
        == r3sm_json["mappings"]
    )
    assert file == r3sm_json["file"]
    assert source_files == r3sm_json["sources"]
    assert r3sm.source_root == r3sm_json["sourceRoot"]

    round_trip = R3SourceMap.from_json(
        r3sm_json, target="\n".join(r.target_extract for r in r3sm.entries.values())
    )

    assert r3sm_json == round_trip.to_json()


C = "comp.compile(with_sourcemap=True)"


def unparse(sourcemap_items):
    return list(map(lambda smi: ast.unparse(smi.frame.node), sourcemap_items))


@pytest.mark.parametrize("mode", Mode)
@pytest.mark.parametrize("version", range(2, 8))
@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_sanity_check(_, mode, version):
    """
    Sanity check source mapping the most important PyTeal constructs

    Cannot utilize @pytest.mark.parametrize because of monkeypatching
    """
    import pyteal as pt

    P = f"#pragma version {version}"
    test_cases = [
        (pt.Int(42), [(P, C), ("int 42", "pt.Int(42)"), ("return", C)]),
        (
            pt.Seq(pt.Pop(pt.Bytes("hello world")), pt.Int(1)),
            [
                (P, C),
                ('byte "hello world"', "pt.Bytes('hello world')"),
                ("pop", "pt.Pop(pt.Bytes('hello world'))"),
                ("int 1", "pt.Int(1)"),
                ("return", C),
            ],
        ),
        (
            pt.Int(2) * pt.Int(3),
            [
                (P, C),
                ("int 2", "pt.Int(2)"),
                ("int 3", "pt.Int(3)"),
                ("*", "pt.Int(2) * pt.Int(3)"),
                ("return", C),
            ],
        ),
    ]

    for i, (expr, line2unparsed) in enumerate(test_cases):
        comp = Compilation(
            expr, mode, version=version, assemble_constants=False, optimize=None
        )
        bundle = comp.compile(with_sourcemap=True)
        sourcemap = bundle.sourcemap

        assert sourcemap
        assert sourcemap.hybrid is True
        assert sourcemap.source_inference is True

        smis = sourcemap.as_list()
        expected_lines, unparsed = list(zip(*line2unparsed))
        assert list(expected_lines) == bundle.lines
        assert list(expected_lines) == sourcemap.teal_chunks
        assert list(unparsed) == unparse(smis)
