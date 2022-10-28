"""
This file monkey-patches ConfigParser in order to enable
source mapping and test the results of source mapping various 
PyTeal apps.
"""

import ast
from asyncore import close_all
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
    is_admin = pt.App.localGet(pt.Int(0), pt.Bytes("admin"))
    transfer = set_admin = mint = register = on_closeout = on_creation = pt.Return(
        pt.Int(1)
    )

    """
    test_cases = [
        (
            pt.Return(pt.Int(42)),
            [(P, C), ("int 42", "pt.Int(42)"), ("return", "pt.Return(pt.Int(42))")],
        ),
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
        (
            pt.Int(2) ^ pt.Int(3),
            [
                (P, C),
                ("int 2", "pt.Int(2)"),
                ("int 3", "pt.Int(3)"),
                ("^", "pt.Int(2) ^ pt.Int(3)"),
                ("return", C),
            ],
        ),
        (
            pt.Int(1) + pt.Int(2) * pt.Int(3),
            [
                (P, C),
                ("int 1", "pt.Int(1)"),
                ("int 2", "pt.Int(2)"),
                ("int 3", "pt.Int(3)"),
                ("*", "pt.Int(2) * pt.Int(3)"),
                ("+", "pt.Int(1) + pt.Int(2) * pt.Int(3)"),
                ("return", C),
            ],
        ),
        (
            ~pt.Int(1),
            [(P, C), ("int 1", "pt.Int(1)"), ("~", "~pt.Int(1)"), ("return", C)],
        ),
        (
            pt.And(
                pt.Int(1),
                pt.Int(2),
                pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6)))),
            ),
            [
                (P, C),
                ("int 1", "pt.Int(1)"),
                ("int 2", "pt.Int(2)"),
                (
                    "&&",
                    "pt.And(pt.Int(1), pt.Int(2), pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6)))))",
                ),
                ("int 3", "pt.Int(3)"),
                ("int 4", "pt.Int(4)"),
                (
                    "||",
                    "pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6))))",
                ),
                ("int 5", "pt.Int(5)"),
                ("int 6", "pt.Int(6)"),
                ("&&", "pt.And(pt.Int(5), pt.Int(6))"),
                (
                    "||",
                    "pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6))))",
                ),
                (
                    "&&",
                    "pt.And(pt.Int(1), pt.Int(2), pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6)))))",
                ),
                ("return", C),
            ],
        ),
        # PyTEAL bugs - the following don't get parsed as expected!
        # (pt.Int(1) != pt.Int(2) == pt.Int(3), [])
        # (
        #     pt.Int(1) + pt.Int(2) - pt.Int(3) * pt.Int(4) / pt.Int(5) % pt.Int(6)
        #     < pt.Int(7)
        #     > pt.Int(8)
        #     <= pt.Int(9) ** pt.Int(10)
        #     != pt.Int(11)
        #     == pt.Int(12),
        #     [],
        # ),
        (
            pt.Btoi(
                pt.BytesAnd(pt.Bytes("base16", "0xBEEF"), pt.Bytes("base16", "0x1337"))
            ),
            [
                (P, C),
                ("byte 0xBEEF", "pt.Bytes('base16', '0xBEEF')"),
                ("byte 0x1337", "pt.Bytes('base16', '0x1337')"),
                (
                    "b&",
                    "pt.BytesAnd(pt.Bytes('base16', '0xBEEF'), pt.Bytes('base16', '0x1337'))",
                ),
                (
                    "btoi",
                    "pt.Btoi(pt.BytesAnd(pt.Bytes('base16', '0xBEEF'), pt.Bytes('base16', '0x1337')))",
                ),
                ("return", C),
            ],
            4,
        ),
        (
            pt.Btoi(pt.BytesZero(pt.Int(4))),
            [
                (P, C),
                ("int 4", "pt.Int(4)"),
                ("bzero", "pt.BytesZero(pt.Int(4))"),
                ("btoi", "pt.Btoi(pt.BytesZero(pt.Int(4)))"),
                ("return", C),
            ],
            4,
        ),
        (
            pt.Btoi(pt.BytesNot(pt.Bytes("base16", "0xFF00"))),
            [
                (P, C),
                ("byte 0xFF00", "pt.Bytes('base16', '0xFF00')"),
                ("b~", "pt.BytesNot(pt.Bytes('base16', '0xFF00'))"),
                ("btoi", "pt.Btoi(pt.BytesNot(pt.Bytes('base16', '0xFF00')))"),
                ("return", C),
            ],
            4,
        ),
        (
            pt.Seq(
                pt.Pop(pt.SetBit(pt.Bytes("base16", "0x00"), pt.Int(3), pt.Int(1))),
                pt.GetBit(pt.Int(16), pt.Int(64)),
            ),
            [
                (P, C),
                ("byte 0x00", "pt.Bytes('base16', '0x00')"),
                ("int 3", "pt.Int(3)"),
                ("int 1", "pt.Int(1)"),
                (
                    "setbit",
                    "pt.SetBit(pt.Bytes('base16', '0x00'), pt.Int(3), pt.Int(1))",
                ),
                (
                    "pop",
                    "pt.Pop(pt.SetBit(pt.Bytes('base16', '0x00'), pt.Int(3), pt.Int(1)))",
                ),
                ("int 16", "pt.Int(16)"),
                ("int 64", "pt.Int(64)"),
                ("getbit", "pt.GetBit(pt.Int(16), pt.Int(64))"),
                ("return", C),
            ],
            3,
        ),
        (
            pt.Seq(
                pt.Pop(pt.SetByte(pt.Bytes("base16", "0xff00"), pt.Int(0), pt.Int(0))),
                pt.GetByte(pt.Bytes("abc"), pt.Int(2)),
            ),
            [
                (P, C),
                ("byte 0xff00", "pt.Bytes('base16', '0xff00')"),
                ("int 0", "pt.Int(0)"),
                ("int 0", "pt.Int(0)"),
                (
                    "setbyte",
                    "pt.SetByte(pt.Bytes('base16', '0xff00'), pt.Int(0), pt.Int(0))",
                ),
                (
                    "pop",
                    "pt.Pop(pt.SetByte(pt.Bytes('base16', '0xff00'), pt.Int(0), pt.Int(0)))",
                ),
                ('byte "abc"', "pt.Bytes('abc')"),
                ("int 2", "pt.Int(2)"),
                ("getbyte", "pt.GetByte(pt.Bytes('abc'), pt.Int(2))"),
                ("return", C),
            ],
            3,
        ),
        (
            pt.Btoi(pt.Concat(pt.Bytes("a"), pt.Bytes("b"), pt.Bytes("c"))),
            [
                (P, C),
                ('byte "a"', "pt.Bytes('a')"),
                ('byte "b"', "pt.Bytes('b')"),
                ("concat", "pt.Concat(pt.Bytes('a'), pt.Bytes('b'), pt.Bytes('c'))"),
                ('byte "c"', "pt.Bytes('c')"),
                ("concat", "pt.Concat(pt.Bytes('a'), pt.Bytes('b'), pt.Bytes('c'))"),
                (
                    "btoi",
                    "pt.Btoi(pt.Concat(pt.Bytes('a'), pt.Bytes('b'), pt.Bytes('c')))",
                ),
                ("return", C),
            ],
        ),
        (
            pt.Btoi(pt.Substring(pt.Bytes("algorand"), pt.Int(2), pt.Int(8))),
            [
                (P, C),
                ('byte "algorand"', "pt.Bytes('algorand')"),
                (
                    "extract 2 6" if version >= 5 else "substring 2 8",
                    "pt.Substring(pt.Bytes('algorand'), pt.Int(2), pt.Int(8))",
                ),
                (
                    "btoi",
                    "pt.Btoi(pt.Substring(pt.Bytes('algorand'), pt.Int(2), pt.Int(8)))",
                ),
                (
                    "return",
                    C,
                ),
            ],
        ),
        (
            pt.Btoi(pt.Extract(pt.Bytes("algorand"), pt.Int(2), pt.Int(6))),
            [
                (P, C),
                ('byte "algorand"', "pt.Bytes('algorand')"),
                (
                    "substring 2 8" if version < 5 else "extract 2 6",
                    "pt.Extract(pt.Bytes('algorand'), pt.Int(2), pt.Int(6))",
                ),
                (
                    "btoi",
                    "pt.Btoi(pt.Extract(pt.Bytes('algorand'), pt.Int(2), pt.Int(6)))",
                ),
                ("return", C),
            ],
            5,
        ),
        (
            pt.And(
                pt.Txn.type_enum() == pt.TxnType.Payment,
                pt.Txn.fee() < pt.Int(100),
                pt.Txn.first_valid() % pt.Int(50) == pt.Int(0),
                pt.Txn.last_valid() == pt.Int(5000) + pt.Txn.first_valid(),
                pt.Txn.lease() == pt.Bytes("base64", "023sdDE2"),
            ),
            [
                (P, C),
                ("txn TypeEnum", "pt.Txn.type_enum()"),
                ("int pay", "pt.Txn.type_enum() == pt.TxnType.Payment"),
                ("==", "pt.Txn.type_enum() == pt.TxnType.Payment"),
                ("txn Fee", "pt.Txn.fee()"),
                ("int 100", "pt.Int(100)"),
                ("<", "pt.Txn.fee() < pt.Int(100)"),
                (
                    "&&",
                    "pt.And(pt.Txn.type_enum() == pt.TxnType.Payment, pt.Txn.fee() < pt.Int(100), pt.Txn.first_valid() % pt.Int(50) == pt.Int(0), pt.Txn.last_valid() == pt.Int(5000) + pt.Txn.first_valid(), pt.Txn.lease() == pt.Bytes('base64', '023sdDE2'))",
                ),
                ("txn FirstValid", "pt.Txn.first_valid()"),
                ("int 50", "pt.Int(50)"),
                ("%", "pt.Txn.first_valid() % pt.Int(50)"),
                ("int 0", "pt.Int(0)"),
                ("==", "pt.Txn.first_valid() % pt.Int(50) == pt.Int(0)"),
                (
                    "&&",
                    "pt.And(pt.Txn.type_enum() == pt.TxnType.Payment, pt.Txn.fee() < pt.Int(100), pt.Txn.first_valid() % pt.Int(50) == pt.Int(0), pt.Txn.last_valid() == pt.Int(5000) + pt.Txn.first_valid(), pt.Txn.lease() == pt.Bytes('base64', '023sdDE2'))",
                ),
                ("txn LastValid", "pt.Txn.last_valid()"),
                ("int 5000", "pt.Int(5000)"),
                ("txn FirstValid", "pt.Txn.first_valid()"),
                ("+", "pt.Int(5000) + pt.Txn.first_valid()"),
                ("==", "pt.Txn.last_valid() == pt.Int(5000) + pt.Txn.first_valid()"),
                (
                    "&&",
                    "pt.And(pt.Txn.type_enum() == pt.TxnType.Payment, pt.Txn.fee() < pt.Int(100), pt.Txn.first_valid() % pt.Int(50) == pt.Int(0), pt.Txn.last_valid() == pt.Int(5000) + pt.Txn.first_valid(), pt.Txn.lease() == pt.Bytes('base64', '023sdDE2'))",
                ),
                ("txn Lease", "pt.Txn.lease()"),
                ("byte base64(023sdDE2)", "pt.Bytes('base64', '023sdDE2')"),
                ("==", "pt.Txn.lease() == pt.Bytes('base64', '023sdDE2')"),
                (
                    "&&",
                    "pt.And(pt.Txn.type_enum() == pt.TxnType.Payment, pt.Txn.fee() < pt.Int(100), pt.Txn.first_valid() % pt.Int(50) == pt.Int(0), pt.Txn.last_valid() == pt.Int(5000) + pt.Txn.first_valid(), pt.Txn.lease() == pt.Bytes('base64', '023sdDE2'))",
                ),
                ("return", C),
            ],
        ),
    ]
    """
    test_cases = [
        (
            pt.Cond(
                [pt.Txn.application_id() == pt.Int(0), on_creation],
                [
                    pt.Txn.on_completion() == pt.OnComplete.DeleteApplication,
                    pt.Return(is_admin),
                ],
                [
                    pt.Txn.on_completion() == pt.OnComplete.UpdateApplication,
                    pt.Return(is_admin),
                ],
                [pt.Txn.on_completion() == pt.OnComplete.CloseOut, on_closeout],
                [pt.Txn.on_completion() == pt.OnComplete.OptIn, register],
                [pt.Txn.application_args[0] == pt.Bytes("set admin"), set_admin],
                [pt.Txn.application_args[0] == pt.Bytes("mint"), mint],
                [pt.Txn.application_args[0] == pt.Bytes("transfer"), transfer],
                [pt.Txn.accounts[4] == pt.Bytes("foo"), on_closeout],
            ),
            [
                (P, C),
                ("txn ApplicationID", "pt.Txn.application_id()"),
                ("int 0", "pt.Int(0)"),
                ("==", "pt.Txn.application_id() == pt.Int(0)"),
                ("bnz main_l18", C),  # ... makes sense
                ("txn OnCompletion", "pt.Txn.on_completion()"),
                (
                    "int DeleteApplication",
                    "pt.Txn.on_completion() == pt.OnComplete.DeleteApplication",
                ),  # source inferencing at work here!!!!
                ("==", "pt.Txn.on_completion() == pt.OnComplete.DeleteApplication"),
                ("bnz main_l17", C),  # makes sense
                ("txn OnCompletion", "pt.Txn.on_completion()"),
                (
                    "int UpdateApplication",
                    "pt.Txn.on_completion() == pt.OnComplete.UpdateApplication",
                ),  # source inferencing
                ("==", "pt.Txn.on_completion() == pt.OnComplete.UpdateApplication"),
                ("bnz main_l16", C),  # yep
                ("txn OnCompletion", "pt.Txn.on_completion()"),
                ("int CloseOut", "pt.Txn.on_completion() == pt.OnComplete.CloseOut"),
                ("==", "pt.Txn.on_completion() == pt.OnComplete.CloseOut"),
                ("bnz main_l15", C),
                ("txn OnCompletion", "pt.Txn.on_completion()"),
                ("int OptIn", "pt.Txn.on_completion() == pt.OnComplete.OptIn"),
                ("==", "pt.Txn.on_completion() == pt.OnComplete.OptIn"),
                ("bnz main_l14", C),
                ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
                ('byte "set admin"', "pt.Bytes('set admin')"),
                ("==", "pt.Txn.application_args[0] == pt.Bytes('set admin')"),
                ("bnz main_l13", C),
                ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
                ('byte "mint"', "pt.Bytes('mint')"),
                ("==", "pt.Txn.application_args[0] == pt.Bytes('mint')"),
                ("bnz main_l12", C),
                ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
                ('byte "transfer"', "pt.Bytes('transfer')"),
                ("==", "pt.Txn.application_args[0] == pt.Bytes('transfer')"),
                ("bnz main_l11", C),
                ("txna Accounts 4", "pt.Txn.accounts[4]"),
                ('byte "foo"', "pt.Bytes('foo')"),
                ("==", "pt.Txn.accounts[4] == pt.Bytes('foo')"),
                ("bnz main_l10", C),
                (
                    "err",
                    "pt.Cond([pt.Txn.application_id() == pt.Int(0), on_creation], [pt.Txn.on_completion() == pt.OnComplete.DeleteApplication, pt.Return(is_admin)], [pt.Txn.on_completion() == pt.OnComplete.UpdateApplication, pt.Return(is_admin)], [pt.Txn.on_completion() == pt.OnComplete.CloseOut, on_closeout], [pt.Txn.on_completion() == pt.OnComplete.OptIn, register], [pt.Txn.application_args[0] == pt.Bytes('set admin'), set_admin], [pt.Txn.application_args[0] == pt.Bytes('mint'), mint], [pt.Txn.application_args[0] == pt.Bytes('transfer'), transfer], [pt.Txn.accounts[4] == pt.Bytes('foo'), on_closeout])",
                ),  # OUCH - this nastiness is from Cond gnerating an err block at the very end!!!
                ("main_l10:", C),
                ("int 1", "pt.Int(1)"),
                ("return", "pt.Return(pt.Int(1))"),
                ("main_l11:", C),
                ("int 1", "pt.Int(1)"),
                ("return", "pt.Return(pt.Int(1))"),
                ("main_l12:", C),
                ("int 1", "pt.Int(1)"),
                ("return", "pt.Return(pt.Int(1))"),
                ("main_l13:", C),
                ("int 1", "pt.Int(1)"),
                ("return", "pt.Return(pt.Int(1))"),
                ("main_l14:", C),
                ("int 1", "pt.Int(1)"),
                ("return", "pt.Return(pt.Int(1))"),
                ("main_l15:", C),
                ("int 1", "pt.Int(1)"),
                ("return", "pt.Return(pt.Int(1))"),
                ("main_l16:", C),
                ("int 0", "pt.Int(0)"),
                ('byte "admin"', "pt.Bytes('admin')"),
                ("app_local_get", "pt.App.localGet(pt.Int(0), pt.Bytes('admin'))"),
                ("return", "pt.Return(is_admin)"),
                ("main_l17:", C),
                ("int 0", "pt.Int(0)"),
                ('byte "admin"', "pt.Bytes('admin')"),
                ("app_local_get", "pt.App.localGet(pt.Int(0), pt.Bytes('admin'))"),
                ("return", "pt.Return(is_admin)"),
                ("main_l18:", C),
                ("int 1", "pt.Int(1)"),
                ("return", "pt.Return(pt.Int(1))"),
            ],
            2,
            Mode.Application,
        ),
    ]

    # TODO: don't merge in the next line:
    test_cases = test_cases[-1:]
    for i, test_case in enumerate(test_cases):
        expr, line2unparsed = test_case[:2]
        if len(test_case) > 2:
            min_version = test_case[2]
            if version < min_version:
                return
        if len(test_case) > 3:
            fixed_mode = test_case[3]
            if mode != fixed_mode:
                return

        comp = Compilation(
            expr, mode, version=version, assemble_constants=False, optimize=None
        )
        bundle = comp.compile(with_sourcemap=True)
        sourcemap = bundle.sourcemap

        msg = f"[{i+1}]. case with {expr=}, {bundle=}"

        assert sourcemap, msg
        assert sourcemap.hybrid is True, msg
        assert sourcemap.source_inference is True, msg

        smis = sourcemap.as_list()
        expected_lines, unparsed = list(zip(*line2unparsed))

        msg = f"{msg}, {smis=}"
        assert list(expected_lines) == bundle.lines, msg
        assert list(expected_lines) == sourcemap.teal_chunks, msg
        assert list(unparsed) == unparse(smis), msg
