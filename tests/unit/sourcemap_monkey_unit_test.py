"""
This file monkey-patches ConfigParser in order to enable source mapping
and test the results of source mapping various PyTeal apps.
"""

import ast
from configparser import ConfigParser
from copy import deepcopy
from pathlib import Path
from typing import cast
from unittest import mock

import pytest

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"

FIXTURES = Path.cwd() / "tests" / "unit" / "sourcemaps"


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_r3sourcemap(_):
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions
    from pyteal.compiler.sourcemap import R3SourceMap

    filename = "dummy filename"
    compile_bundle = router.compile(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        approval_filename=filename,
        with_sourcemaps=True,
    )

    ptsm = compile_bundle.approval_sourcemap
    assert ptsm

    r3sm = ptsm._cached_r3sourcemap
    assert r3sm

    assert filename == r3sm.file
    assert cast(str, r3sm.source_root).endswith("/pyteal/")
    assert list(range(len(r3sm.entries))) == [l for l, _ in r3sm.entries]
    assert all(c == 0 for _, c in r3sm.entries)
    assert all(x == (0,) for x in r3sm.index)
    assert len(r3sm.entries) == len(r3sm.index)

    this_file = __file__.split("/")[-1]
    source_files = [
        "examples/application/abi/algobank.py",
        f"tests/unit/{this_file}",
    ]
    assert source_files == r3sm.source_files

    r3sm_json = r3sm.to_json()

    assert "mappings" in r3sm_json
    assert (
        "AAgBS;AAAA;AAAA;AAAA;ACUT;ADgBA;AAAA;AAAA;AChBA;ADwCA;AAAA;AAAA;ACxCA;ADqDA;AAAA;AAAA;ACrDA;AAAA;AAAA;ADqDA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACrDA;AAAA;ADqDA;AAAA;AAAA;ACrDA;ADwCA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACxCA;AAAA;AAAA;AAAA;AAAA;ADwCA;AAAA;ACxCA;ADgBA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AChBA;AAAA;ADgBA;AAAA;AAAA;AA1BS;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAJL;AACc;AAAd;AAA4C;AAAc;AAA3B;AAA/B;AAFuB;AAKlB;AAAA;AAAA;AAM8B;AAAA;AAN9B;AAAA;AAAA;AAAA;AAAA;AAI6B;AAAA;AAJ7B;AAAA;AAAA;AATS;AAAgB;AAAhB;AAAP;ACmBX;AAAA;AAAA;AAAA;AAAA;AAAA;AD6Be;AAAA;AAA0B;AAAA;AAA1B;AAAP;AACO;AAAA;AAA4B;AAA5B;AAAP;AAEI;AAAA;AACA;AACa;AAAA;AAAkB;AAA/B;AAAmD;AAAA;AAAnD;AAHJ;AC/BR;ADwCA;AAAA;AAAA;AASmC;AAAgB;AAA7B;ACjDtB;AAAA;AAAA;AAAA;AAAA;AAAA;ADyEY;AACA;AACa;AAAc;AAA3B;AAA+C;AAA/C;AAHJ;AAKA;AACA;AAAA;AAG2B;AAAA;AAH3B;AAIyB;AAJzB;AAKsB;AALtB;AAQA;AAAA"
        == r3sm_json["mappings"]
    )

    assert "file" in r3sm_json
    assert filename == r3sm_json["file"]

    assert "sources" in r3sm_json
    assert source_files == r3sm_json["sources"]

    assert "sourceRoot" in r3sm_json
    assert r3sm.source_root == r3sm_json["sourceRoot"]

    target = "\n".join(r.target_extract for r in r3sm.entries.values())  # type: ignore
    round_trip = R3SourceMap.from_json(r3sm_json, target=target)

    assert r3sm_json == round_trip.to_json()


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_reconstruct(_):
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    compile_bundle = router.compile(
        version=6, optimize=OptimizeOptions(scratch_slots=True), with_sourcemaps=True
    )

    assert compile_bundle.approval_sourcemap
    assert compile_bundle.clear_sourcemap

    with open(ALGOBANK / "algobank_approval.teal") as af:
        assert af.read() == compile_bundle.approval_sourcemap.pure_teal()

    with open(ALGOBANK / "algobank_clear_state.teal") as cf:
        assert cf.read() == compile_bundle.clear_sourcemap.pure_teal()


# def fixture_comparison(sourcemap, name: str):
#     from pyteal.compiler.sourcemap import PyTealSourceMap

#     assert isinstance(sourcemap, PyTealSourceMap)
#     new_version = sourcemap._tabulate_for_dev()
#     with open(FIXTURES / f"_{name}", "w") as f:
#         f.write(new_version)

#     not_actually_comparing = False
#     if not_actually_comparing:
#         return

#     with open(FIXTURES / name) as f:
#         old_version = f.read()

#     assert old_version == new_version


# @mock.patch.object(ConfigParser, "getboolean", return_value=True)
# @pytest.mark.parametrize("version", [6])
# @pytest.mark.parametrize("source_inference", [False, True])
# @pytest.mark.parametrize("assemble_constants", [False, True])
# @pytest.mark.parametrize("optimize_slots", [False, True])
# def test_sourcemaps(_, version, source_inference, assemble_constants, optimize_slots):
#     from examples.application.abi.algobank import router
#     from pyteal import OptimizeOptions

#     # TODO: add functionality that tallies the line statuses up and assert that all
#     # statuses were > SourceMapItemStatus.PYTEAL_GENERATED

#     compile_bundle = router.compile_program_with_sourcemaps(
#         version=version,
#         assemble_constants=assemble_constants,
#         optimize=OptimizeOptions(scratch_slots=optimize_slots),
#         source_inference=source_inference,
#     )

#     assert compile_bundle.approval_sourcemap
#     assert compile_bundle.clear_sourcemap

#     suffix = f"_v{version}_si{int(source_inference)}_ac{int(assemble_constants)}_ozs{int(optimize_slots)}"
#     fixture_comparison(
#         compile_bundle.approval_sourcemap, f"algobank_approval{suffix}.txt"
#     )
#     fixture_comparison(compile_bundle.clear_sourcemap, f"algobank_clear{suffix}.txt")


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_mocked_config_for_frames(_):
    config = ConfigParser()
    assert config.getboolean("pyteal-source-mapper", "enabled") is True
    from pyteal.stack_frame import Frames

    assert Frames.skipping_all() is False
    assert Frames.skipping_all(_force_refresh=True) is False


# TODO: ???this is temporary????


def make(x, y, z):
    import pyteal as pt

    return pt.Int(x) + pt.Int(y) + pt.Int(z)


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_lots_o_indirection(_):
    import pyteal as pt

    e1 = pt.Seq(pt.Pop(make(1, 2, 3)), pt.Pop(make(4, 5, 6)), make(7, 8, 9))

    @pt.Subroutine(pt.TealType.uint64)
    def foo(x):
        return pt.Seq(pt.Pop(e1), e1)

    pt.Compilation(foo(pt.Int(42)), pt.Mode.Application, version=6).compile(
        with_sourcemap=True
    )


# ### ----------------- SANITY CHECKS SURVEY MOST PYTEAL CONSTRUCTS ----------------- ### #

P = "#pragma version {v}"  # fill the template at runtime

C = "comp.compile(with_sourcemap=True)"

BIG_A = "pt.And(pt.Gtxn[0].rekey_to() == pt.Global.zero_address(), pt.Gtxn[1].rekey_to() == pt.Global.zero_address(), pt.Gtxn[2].rekey_to() == pt.Global.zero_address(), pt.Gtxn[3].rekey_to() == pt.Global.zero_address(), pt.Gtxn[4].rekey_to() == pt.Global.zero_address(), pt.Gtxn[0].last_valid() == pt.Gtxn[1].last_valid(), pt.Gtxn[1].last_valid() == pt.Gtxn[2].last_valid(), pt.Gtxn[2].last_valid() == pt.Gtxn[3].last_valid(), pt.Gtxn[3].last_valid() == pt.Gtxn[4].last_valid(), pt.Gtxn[0].type_enum() == pt.TxnType.AssetTransfer, pt.Gtxn[0].xfer_asset() == asset_c, pt.Gtxn[0].receiver() == receiver)"
BIG_OR = "pt.Or(pt.App.globalGet(pt.Bytes('paused')), pt.App.localGet(pt.Int(0), pt.Bytes('frozen')), pt.App.localGet(pt.Int(1), pt.Bytes('frozen')), pt.App.localGet(pt.Int(0), pt.Bytes('lock until')) >= pt.Global.latest_timestamp(), pt.App.localGet(pt.Int(1), pt.Bytes('lock until')) >= pt.Global.latest_timestamp(), pt.App.globalGet(pt.Concat(pt.Bytes('rule'), pt.Itob(pt.App.localGet(pt.Int(0), pt.Bytes('transfer group'))), pt.Itob(pt.App.localGet(pt.Int(1), pt.Bytes('transfer group'))))))"
BIG_C = "pt.Cond([pt.Txn.application_id() == pt.Int(0), foo], [pt.Txn.on_completion() == pt.OnComplete.DeleteApplication, pt.Return(is_admin)], [pt.Txn.on_completion() == pt.OnComplete.UpdateApplication, pt.Return(is_admin)], [pt.Txn.on_completion() == pt.OnComplete.CloseOut, foo], [pt.Txn.on_completion() == pt.OnComplete.OptIn, foo], [pt.Txn.application_args[0] == pt.Bytes('set admin'), foo], [pt.Txn.application_args[0] == pt.Bytes('mint'), foo], [pt.Txn.application_args[0] == pt.Bytes('transfer'), foo], [pt.Txn.accounts[4] == pt.Bytes('foo'), foo])"
BIG_W = "pt.While(i.load() < pt.Global.group_size())"
BIG_F = "pt.For(i.store(pt.Int(0)), i.load() < pt.Global.group_size(), i.store(i.load() + pt.Int(1)))"

"""
    asset_c = pt.Tmpl.Int("TMPL_ASSET_C")
    receiver = pt.Tmpl.Addr("TMPL_RECEIVER")
    transfer_amount = pt.Btoi(pt.Txn.application_args[1])
"""

# is_admin = pt.App.localGet(pt.Int(0), pt.Bytes("admin"))
# transfer = set_admin = mint = register = on_closeout = on_creation = pt.Return(pt.Int(1))
#     pt.Int(1)
# )
# asset_c = pt.Tmpl.Int("TMPL_ASSET_C")
# receiver = pt.Tmpl.Addr("TMPL_RECEIVER")
# transfer_amount = pt.Btoi(pt.Txn.application_args[1])

CONSTRUCTS = [
    (
        lambda pt: pt.Return(pt.Int(42)),
        [[P, C], ["int 42", "pt.Int(42)"], ["return", "pt.Return(pt.Int(42))"]],
    ),
    (lambda pt: pt.Int(42), [[P, C], ["int 42", "pt.Int(42)"], ["return", C]]),
    (
        lambda pt: pt.Seq(pt.Pop(pt.Bytes("hello world")), pt.Int(1)),
        [
            [P, C],
            ['byte "hello world"', "pt.Bytes('hello world')"],
            ["pop", "pt.Pop(pt.Bytes('hello world'))"],
            ["int 1", "pt.Int(1)"],
            ["return", C],
        ],
    ),
    (
        lambda pt: pt.Int(2) * pt.Int(3),
        [
            [P, C],
            ["int 2", "pt.Int(2)"],
            ["int 3", "pt.Int(3)"],
            ["*", "pt.Int(2) * pt.Int(3)"],
            ["return", C],
        ],
    ),
    (
        lambda pt: pt.Int(2) ^ pt.Int(3),
        [
            [P, C],
            ["int 2", "pt.Int(2)"],
            ["int 3", "pt.Int(3)"],
            ["^", "pt.Int(2) ^ pt.Int(3)"],
            ["return", C],
        ],
    ),
    (
        lambda pt: pt.Int(1) + pt.Int(2) * pt.Int(3),
        [
            [P, C],
            ["int 1", "pt.Int(1)"],
            ["int 2", "pt.Int(2)"],
            ["int 3", "pt.Int(3)"],
            ["*", "pt.Int(2) * pt.Int(3)"],
            ["+", "pt.Int(1) + pt.Int(2) * pt.Int(3)"],
            ["return", C],
        ],
    ),
    (
        lambda pt: ~pt.Int(1),
        [[P, C], ["int 1", "pt.Int(1)"], ["~", "~pt.Int(1)"], ["return", C]],
    ),
    (
        lambda pt: pt.And(
            pt.Int(1),
            pt.Int(2),
            pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6)))),
        ),
        [
            [P, C],
            ["int 1", "pt.Int(1)"],
            ["int 2", "pt.Int(2)"],
            [
                "&&",
                "pt.And(pt.Int(1), pt.Int(2), pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6)))))",
            ],
            ["int 3", "pt.Int(3)"],
            ["int 4", "pt.Int(4)"],
            [
                "||",
                "pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6))))",
            ],
            ["int 5", "pt.Int(5)"],
            ["int 6", "pt.Int(6)"],
            ["&&", "pt.And(pt.Int(5), pt.Int(6))"],
            [
                "||",
                "pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6))))",
            ],
            [
                "&&",
                "pt.And(pt.Int(1), pt.Int(2), pt.Or(pt.Int(3), pt.Int(4), pt.Or(pt.And(pt.Int(5), pt.Int(6)))))",
            ],
            ["return", C],
        ],
    ),
    (
        lambda pt: pt.Btoi(
            pt.BytesAnd(pt.Bytes("base16", "0xBEEF"), pt.Bytes("base16", "0x1337"))
        ),
        [
            [P, C],
            ["byte 0xBEEF", "pt.Bytes('base16', '0xBEEF')"],
            ["byte 0x1337", "pt.Bytes('base16', '0x1337')"],
            [
                "b&",
                "pt.BytesAnd(pt.Bytes('base16', '0xBEEF'), pt.Bytes('base16', '0x1337'))",
            ],
            [
                "btoi",
                "pt.Btoi(pt.BytesAnd(pt.Bytes('base16', '0xBEEF'), pt.Bytes('base16', '0x1337')))",
            ],
            ["return", C],
        ],
        4,
    ),
    (
        lambda pt: pt.Btoi(pt.BytesZero(pt.Int(4))),
        [
            [P, C],
            ["int 4", "pt.Int(4)"],
            ["bzero", "pt.BytesZero(pt.Int(4))"],
            ["btoi", "pt.Btoi(pt.BytesZero(pt.Int(4)))"],
            ["return", C],
        ],
        4,
    ),
    (
        lambda pt: pt.Btoi(pt.BytesNot(pt.Bytes("base16", "0xFF00"))),
        [
            [P, C],
            ["byte 0xFF00", "pt.Bytes('base16', '0xFF00')"],
            ["b~", "pt.BytesNot(pt.Bytes('base16', '0xFF00'))"],
            ["btoi", "pt.Btoi(pt.BytesNot(pt.Bytes('base16', '0xFF00')))"],
            ["return", C],
        ],
        4,
    ),
    (
        lambda pt: pt.Seq(
            pt.Pop(pt.SetBit(pt.Bytes("base16", "0x00"), pt.Int(3), pt.Int(1))),
            pt.GetBit(pt.Int(16), pt.Int(64)),
        ),
        [
            [P, C],
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
        lambda pt: pt.Seq(
            pt.Pop(pt.SetByte(pt.Bytes("base16", "0xff00"), pt.Int(0), pt.Int(0))),
            pt.GetByte(pt.Bytes("abc"), pt.Int(2)),
        ),
        [
            [P, C],
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
        lambda pt: pt.Btoi(pt.Concat(pt.Bytes("a"), pt.Bytes("b"), pt.Bytes("c"))),
        [
            [P, C],
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
        lambda pt: pt.Btoi(pt.Substring(pt.Bytes("algorand"), pt.Int(2), pt.Int(8))),
        [
            [P, C],
            ('byte "algorand"', "pt.Bytes('algorand')"),
            (
                "extract 2 6",
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
        5,
    ),
    (
        lambda pt: pt.Btoi(pt.Extract(pt.Bytes("algorand"), pt.Int(2), pt.Int(6))),
        [
            [P, C],
            ('byte "algorand"', "pt.Bytes('algorand')"),
            (
                "extract 2 6",
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
        lambda pt: pt.And(
            pt.Txn.type_enum() == pt.TxnType.Payment,
            pt.Txn.fee() < pt.Int(100),
            pt.Txn.first_valid() % pt.Int(50) == pt.Int(0),
            pt.Txn.last_valid() == pt.Int(5000) + pt.Txn.first_valid(),
            pt.Txn.lease() == pt.Bytes("base64", "023sdDE2"),
        ),
        [
            [P, C],
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
    (
        lambda pt: [
            is_admin := pt.App.localGet(pt.Int(0), pt.Bytes("admin")),
            foo := pt.Return(pt.Int(1)),
            pt.Cond(
                [pt.Txn.application_id() == pt.Int(0), foo],
                [
                    pt.Txn.on_completion() == pt.OnComplete.DeleteApplication,
                    pt.Return(is_admin),
                ],
                [
                    pt.Txn.on_completion() == pt.OnComplete.UpdateApplication,
                    pt.Return(is_admin),
                ],
                [pt.Txn.on_completion() == pt.OnComplete.CloseOut, foo],
                [pt.Txn.on_completion() == pt.OnComplete.OptIn, foo],
                [pt.Txn.application_args[0] == pt.Bytes("set admin"), foo],
                [pt.Txn.application_args[0] == pt.Bytes("mint"), foo],
                [pt.Txn.application_args[0] == pt.Bytes("transfer"), foo],
                [pt.Txn.accounts[4] == pt.Bytes("foo"), foo],
            ),
        ][-1],
        [
            [P, C],
            ("txn ApplicationID", "pt.Txn.application_id()"),
            ("int 0", "pt.Int(0)"),
            ("==", "pt.Txn.application_id() == pt.Int(0)"),
            ("bnz main_l18", BIG_C),  # ... makes sense
            ("txn OnCompletion", "pt.Txn.on_completion()"),
            (
                "int DeleteApplication",
                "pt.Txn.on_completion() == pt.OnComplete.DeleteApplication",
            ),  # source inferencing at work here!!!!
            ("==", "pt.Txn.on_completion() == pt.OnComplete.DeleteApplication"),
            ("bnz main_l17", BIG_C),  # makes sense
            ("txn OnCompletion", "pt.Txn.on_completion()"),
            (
                "int UpdateApplication",
                "pt.Txn.on_completion() == pt.OnComplete.UpdateApplication",
            ),  # source inferencing
            ("==", "pt.Txn.on_completion() == pt.OnComplete.UpdateApplication"),
            ("bnz main_l16", BIG_C),  # yep
            ("txn OnCompletion", "pt.Txn.on_completion()"),
            ("int CloseOut", "pt.Txn.on_completion() == pt.OnComplete.CloseOut"),
            ("==", "pt.Txn.on_completion() == pt.OnComplete.CloseOut"),
            ("bnz main_l15", BIG_C),
            ("txn OnCompletion", "pt.Txn.on_completion()"),
            ("int OptIn", "pt.Txn.on_completion() == pt.OnComplete.OptIn"),
            ("==", "pt.Txn.on_completion() == pt.OnComplete.OptIn"),
            ("bnz main_l14", BIG_C),
            ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
            ('byte "set admin"', "pt.Bytes('set admin')"),
            ("==", "pt.Txn.application_args[0] == pt.Bytes('set admin')"),
            ("bnz main_l13", BIG_C),
            ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
            ('byte "mint"', "pt.Bytes('mint')"),
            ("==", "pt.Txn.application_args[0] == pt.Bytes('mint')"),
            ("bnz main_l12", BIG_C),
            ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
            ('byte "transfer"', "pt.Bytes('transfer')"),
            ("==", "pt.Txn.application_args[0] == pt.Bytes('transfer')"),
            ("bnz main_l11", BIG_C),
            ("txna Accounts 4", "pt.Txn.accounts[4]"),
            ('byte "foo"', "pt.Bytes('foo')"),
            ("==", "pt.Txn.accounts[4] == pt.Bytes('foo')"),
            ("bnz main_l10", BIG_C),
            ("err", BIG_C),
            ("main_l10:", BIG_C),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l11:", BIG_C),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l12:", BIG_C),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l13:", BIG_C),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l14:", BIG_C),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l15:", BIG_C),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l16:", BIG_C),
            ("int 0", "pt.Int(0)"),
            ('byte "admin"', "pt.Bytes('admin')"),
            ("app_local_get", "pt.App.localGet(pt.Int(0), pt.Bytes('admin'))"),
            ("return", "pt.Return(is_admin)"),
            ("main_l17:", BIG_C),
            ("int 0", "pt.Int(0)"),
            ('byte "admin"', "pt.Bytes('admin')"),
            ("app_local_get", "pt.App.localGet(pt.Int(0), pt.Bytes('admin'))"),
            ("return", "pt.Return(is_admin)"),
            ("main_l18:", BIG_C),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
        ],
        2,
        "Application",
    ),
    (
        lambda pt: [
            asset_c := pt.Tmpl.Int("TMPL_ASSET_C"),
            receiver := pt.Tmpl.Addr("TMPL_RECEIVER"),
            pt.And(
                pt.Gtxn[0].rekey_to() == pt.Global.zero_address(),
                pt.Gtxn[1].rekey_to() == pt.Global.zero_address(),
                pt.Gtxn[2].rekey_to() == pt.Global.zero_address(),
                pt.Gtxn[3].rekey_to() == pt.Global.zero_address(),
                pt.Gtxn[4].rekey_to() == pt.Global.zero_address(),
                pt.Gtxn[0].last_valid() == pt.Gtxn[1].last_valid(),
                pt.Gtxn[1].last_valid() == pt.Gtxn[2].last_valid(),
                pt.Gtxn[2].last_valid() == pt.Gtxn[3].last_valid(),
                pt.Gtxn[3].last_valid() == pt.Gtxn[4].last_valid(),
                pt.Gtxn[0].type_enum() == pt.TxnType.AssetTransfer,
                pt.Gtxn[0].xfer_asset() == asset_c,
                pt.Gtxn[0].receiver() == receiver,
            ),
        ][-1],
        [
            [P, C],
            ("gtxn 0 RekeyTo", "pt.Gtxn[0].rekey_to()"),
            ("global ZeroAddress", "pt.Global.zero_address()"),
            ("==", "pt.Gtxn[0].rekey_to() == pt.Global.zero_address()"),
            ("gtxn 1 RekeyTo", "pt.Gtxn[1].rekey_to()"),
            ("global ZeroAddress", "pt.Global.zero_address()"),
            ("==", "pt.Gtxn[1].rekey_to() == pt.Global.zero_address()"),
            ("&&", BIG_A),
            ("gtxn 2 RekeyTo", "pt.Gtxn[2].rekey_to()"),
            ("global ZeroAddress", "pt.Global.zero_address()"),
            ("==", "pt.Gtxn[2].rekey_to() == pt.Global.zero_address()"),
            ("&&", BIG_A),
            ("gtxn 3 RekeyTo", "pt.Gtxn[3].rekey_to()"),
            ("global ZeroAddress", "pt.Global.zero_address()"),
            ("==", "pt.Gtxn[3].rekey_to() == pt.Global.zero_address()"),
            ("&&", BIG_A),
            ("gtxn 4 RekeyTo", "pt.Gtxn[4].rekey_to()"),
            ("global ZeroAddress", "pt.Global.zero_address()"),
            ("==", "pt.Gtxn[4].rekey_to() == pt.Global.zero_address()"),
            ("&&", BIG_A),
            ("gtxn 0 LastValid", "pt.Gtxn[0].last_valid()"),
            ("gtxn 1 LastValid", "pt.Gtxn[1].last_valid()"),
            ("==", "pt.Gtxn[0].last_valid() == pt.Gtxn[1].last_valid()"),
            ("&&", BIG_A),
            ("gtxn 1 LastValid", "pt.Gtxn[1].last_valid()"),
            ("gtxn 2 LastValid", "pt.Gtxn[2].last_valid()"),
            ("==", "pt.Gtxn[1].last_valid() == pt.Gtxn[2].last_valid()"),
            ("&&", BIG_A),
            ("gtxn 2 LastValid", "pt.Gtxn[2].last_valid()"),
            ("gtxn 3 LastValid", "pt.Gtxn[3].last_valid()"),
            ("==", "pt.Gtxn[2].last_valid() == pt.Gtxn[3].last_valid()"),
            ("&&", BIG_A),
            ("gtxn 3 LastValid", "pt.Gtxn[3].last_valid()"),
            ("gtxn 4 LastValid", "pt.Gtxn[4].last_valid()"),
            ("==", "pt.Gtxn[3].last_valid() == pt.Gtxn[4].last_valid()"),
            ("&&", BIG_A),
            ("gtxn 0 TypeEnum", "pt.Gtxn[0].type_enum()"),
            (
                "int axfer",
                "pt.Gtxn[0].type_enum() == pt.TxnType.AssetTransfer",
            ),  # source inference
            ("==", "pt.Gtxn[0].type_enum() == pt.TxnType.AssetTransfer"),
            ("&&", BIG_A),
            ("gtxn 0 XferAsset", "pt.Gtxn[0].xfer_asset()"),
            ("int TMPL_ASSET_C", "pt.Tmpl.Int('TMPL_ASSET_C')"),
            ("==", "pt.Gtxn[0].xfer_asset() == asset_c"),
            ("&&", BIG_A),
            ("gtxn 0 Receiver", "pt.Gtxn[0].receiver()"),
            ("addr TMPL_RECEIVER", "pt.Tmpl.Addr('TMPL_RECEIVER')"),
            ("==", "pt.Gtxn[0].receiver() == receiver"),
            ("&&", BIG_A),
            ("return", C),
        ],
    ),
    (
        lambda pt: pt.And(
            pt.Txn.application_args.length(),  # get the number of application arguments in the transaction
            # as of AVM v5, PyTeal expressions can be used to dynamically index into array properties as well
            pt.Btoi(
                pt.Txn.application_args[pt.Txn.application_args.length() - pt.Int(1)]
            ),
        ),
        [
            [P, C],
            ("txn NumAppArgs", "pt.Txn.application_args.length()"),
            ("txn NumAppArgs", "pt.Txn.application_args.length()"),
            ("int 1", "pt.Int(1)"),
            ("-", "pt.Txn.application_args.length() - pt.Int(1)"),
            (
                "txnas ApplicationArgs",
                "pt.Txn.application_args[pt.Txn.application_args.length() - pt.Int(1)]",
            ),
            (
                "btoi",
                "pt.Btoi(pt.Txn.application_args[pt.Txn.application_args.length() - pt.Int(1)])",
            ),
            (
                "&&",
                "pt.And(pt.Txn.application_args.length(), pt.Btoi(pt.Txn.application_args[pt.Txn.application_args.length() - pt.Int(1)]))",
            ),
            ("return", C),
        ],
        5,
    ),
    (
        lambda pt: pt.Seq(
            receiver_max_balance := pt.App.localGetEx(  # noqa: F841
                pt.Int(1), pt.App.id(), pt.Bytes("max balance")
            ),
            pt.Or(
                pt.App.globalGet(pt.Bytes("paused")),
                pt.App.localGet(pt.Int(0), pt.Bytes("frozen")),
                pt.App.localGet(pt.Int(1), pt.Bytes("frozen")),
                pt.App.localGet(pt.Int(0), pt.Bytes("lock until"))
                >= pt.Global.latest_timestamp(),
                pt.App.localGet(pt.Int(1), pt.Bytes("lock until"))
                >= pt.Global.latest_timestamp(),
                pt.App.globalGet(
                    pt.Concat(
                        pt.Bytes("rule"),
                        pt.Itob(pt.App.localGet(pt.Int(0), pt.Bytes("transfer group"))),
                        pt.Itob(pt.App.localGet(pt.Int(1), pt.Bytes("transfer group"))),
                    )
                ),
            ),
        ),
        [
            [P, C],
            ("int 1", "pt.Int(1)"),
            ("global CurrentApplicationID", "pt.App.id()"),
            ('byte "max balance"', "pt.Bytes('max balance')"),
            (
                "app_local_get_ex",
                "pt.App.localGetEx(pt.Int(1), pt.App.id(), pt.Bytes('max balance'))",
            ),
            ("store 1", C),  # TODO: can be improved if handle maybe/multi-values
            ("store 0", C),
            ('byte "paused"', "pt.Bytes('paused')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('paused'))"),
            ("int 0", "pt.Int(0)"),
            ('byte "frozen"', "pt.Bytes('frozen')"),
            ("app_local_get", "pt.App.localGet(pt.Int(0), pt.Bytes('frozen'))"),
            ("||", BIG_OR),
            ("int 1", "pt.Int(1)"),
            ('byte "frozen"', "pt.Bytes('frozen')"),
            ("app_local_get", "pt.App.localGet(pt.Int(1), pt.Bytes('frozen'))"),
            ("||", BIG_OR),
            ("int 0", "pt.Int(0)"),
            ('byte "lock until"', "pt.Bytes('lock until')"),
            ("app_local_get", "pt.App.localGet(pt.Int(0), pt.Bytes('lock until'))"),
            ("global LatestTimestamp", "pt.Global.latest_timestamp()"),
            (
                ">=",
                "pt.App.localGet(pt.Int(0), pt.Bytes('lock until')) >= pt.Global.latest_timestamp()",
            ),
            ("||", BIG_OR),
            ("int 1", "pt.Int(1)"),
            ('byte "lock until"', "pt.Bytes('lock until')"),
            ("app_local_get", "pt.App.localGet(pt.Int(1), pt.Bytes('lock until'))"),
            ("global LatestTimestamp", "pt.Global.latest_timestamp()"),
            (
                ">=",
                "pt.App.localGet(pt.Int(1), pt.Bytes('lock until')) >= pt.Global.latest_timestamp()",
            ),
            ("||", BIG_OR),
            ('byte "rule"', "pt.Bytes('rule')"),
            ("int 0", "pt.Int(0)"),
            ('byte "transfer group"', "pt.Bytes('transfer group')"),
            (
                "app_local_get",
                "pt.App.localGet(pt.Int(0), pt.Bytes('transfer group'))",
            ),
            (
                "itob",
                "pt.Itob(pt.App.localGet(pt.Int(0), pt.Bytes('transfer group')))",
            ),
            (
                "concat",
                "pt.Concat(pt.Bytes('rule'), pt.Itob(pt.App.localGet(pt.Int(0), pt.Bytes('transfer group'))), pt.Itob(pt.App.localGet(pt.Int(1), pt.Bytes('transfer group'))))",
            ),
            ("int 1", "pt.Int(1)"),
            ('byte "transfer group"', "pt.Bytes('transfer group')"),
            (
                "app_local_get",
                "pt.App.localGet(pt.Int(1), pt.Bytes('transfer group'))",
            ),
            ("itob", "pt.Itob(pt.App.localGet(pt.Int(1), pt.Bytes('transfer group')))"),
            (
                "concat",
                "pt.Concat(pt.Bytes('rule'), pt.Itob(pt.App.localGet(pt.Int(0), pt.Bytes('transfer group'))), pt.Itob(pt.App.localGet(pt.Int(1), pt.Bytes('transfer group'))))",
            ),
            (
                "app_global_get",
                "pt.App.globalGet(pt.Concat(pt.Bytes('rule'), pt.Itob(pt.App.localGet(pt.Int(0), pt.Bytes('transfer group'))), pt.Itob(pt.App.localGet(pt.Int(1), pt.Bytes('transfer group')))))",
            ),
            ("||", BIG_OR),
            ("return", C),
        ],
        2,
        "Application",
    ),
    (
        lambda pt: pt.EcdsaVerify(
            pt.EcdsaCurve.Secp256k1,
            pt.Sha512_256(pt.Bytes("testdata")),
            pt.Bytes(
                "base16",
                "33602297203d2753372cea7794ffe1756a278cbc4907b15a0dd132c9fb82555e",
            ),
            pt.Bytes(
                "base16",
                "20f112126cf3e2eac6e8d4f97a403d21bab07b8dbb77154511bb7b07c0173195",
            ),
            (
                pt.Bytes(
                    "base16",
                    "d6143a58c90c06b594e4414cb788659c2805e0056b1dfceea32c03f59efec517",
                ),
                pt.Bytes(
                    "base16",
                    "00bd2400c479efe5ea556f37e1dc11ccb20f1e642dbfe00ca346fffeae508298",
                ),
            ),
        ),
        [
            [P, C],
            ['byte "testdata"', "pt.Bytes('testdata')"],
            ["sha512_256", "pt.Sha512_256(pt.Bytes('testdata'))"],
            [
                "byte 0x33602297203d2753372cea7794ffe1756a278cbc4907b15a0dd132c9fb82555e",
                "pt.Bytes('base16', '33602297203d2753372cea7794ffe1756a278cbc4907b15a0dd132c9fb82555e')",
            ],
            [
                "byte 0x20f112126cf3e2eac6e8d4f97a403d21bab07b8dbb77154511bb7b07c0173195",
                "pt.Bytes('base16', '20f112126cf3e2eac6e8d4f97a403d21bab07b8dbb77154511bb7b07c0173195')",
            ],
            [
                "byte 0xd6143a58c90c06b594e4414cb788659c2805e0056b1dfceea32c03f59efec517",
                "pt.Bytes('base16', 'd6143a58c90c06b594e4414cb788659c2805e0056b1dfceea32c03f59efec517')",
            ],
            [
                "byte 0x00bd2400c479efe5ea556f37e1dc11ccb20f1e642dbfe00ca346fffeae508298",
                "pt.Bytes('base16', '00bd2400c479efe5ea556f37e1dc11ccb20f1e642dbfe00ca346fffeae508298')",
            ],
            [
                "ecdsa_verify Secp256k1",
                "pt.EcdsaVerify(pt.EcdsaCurve.Secp256k1, pt.Sha512_256(pt.Bytes('testdata')), pt.Bytes('base16', '33602297203d2753372cea7794ffe1756a278cbc4907b15a0dd132c9fb82555e'), pt.Bytes('base16', '20f112126cf3e2eac6e8d4f97a403d21bab07b8dbb77154511bb7b07c0173195'), (pt.Bytes('base16', 'd6143a58c90c06b594e4414cb788659c2805e0056b1dfceea32c03f59efec517'), pt.Bytes('base16', '00bd2400c479efe5ea556f37e1dc11ccb20f1e642dbfe00ca346fffeae508298')))",
            ],
            ["return", C],
        ],
        5,
    ),
    (
        lambda pt: [
            myvar := pt.ScratchVar(
                pt.TealType.uint64
            ),  # assign a scratch slot in any available slot
            anotherVar := pt.ScratchVar(
                pt.TealType.bytes, 4
            ),  # assign this scratch slot to slot #4
            pt.Seq(
                [
                    myvar.store(pt.Int(5)),
                    anotherVar.store(pt.Bytes("hello")),
                    pt.Assert(myvar.load() == pt.Int(5)),
                    pt.Return(pt.Int(1)),
                ]
            ),
        ][-1],
        [
            [P, C],
            ["int 5", "pt.Int(5)"],
            ["store 0", "myvar.store(pt.Int(5))"],
            ['byte "hello"', "pt.Bytes('hello')"],
            ["store 4", "anotherVar.store(pt.Bytes('hello'))"],
            ["load 0", "myvar.load()"],
            ["int 5", "pt.Int(5)"],
            ["==", "myvar.load() == pt.Int(5)"],
            ["assert", "pt.Assert(myvar.load() == pt.Int(5))"],
            ["int 1", "pt.Int(1)"],
            ["return", "pt.Return(pt.Int(1))"],
        ],
        3,
    ),
    (
        lambda pt: [
            s := pt.ScratchVar(pt.TealType.uint64),
            d := pt.DynamicScratchVar(pt.TealType.uint64),
            pt.Seq(
                d.set_index(s),
                s.store(pt.Int(7)),
                d.store(d.load() + pt.Int(3)),
                pt.Assert(s.load() == pt.Int(10)),
                pt.Int(1),
            ),
        ][-1],
        [
            [P, C],
            ["int 0", "d.set_index(s)"],
            ["store 1", "d.set_index(s)"],
            ["int 7", "pt.Int(7)"],
            ["store 0", "s.store(pt.Int(7))"],
            ["load 1", "d.store(d.load() + pt.Int(3))"],
            ["load 1", "d.load()"],
            ["loads", "d.load()"],
            ["int 3", "pt.Int(3)"],
            ["+", "d.load() + pt.Int(3)"],
            ["stores", "d.store(d.load() + pt.Int(3))"],
            ["load 0", "s.load()"],
            ["int 10", "pt.Int(10)"],
            ["==", "s.load() == pt.Int(10)"],
            ["assert", "pt.Assert(s.load() == pt.Int(10))"],
            ["int 1", "pt.Int(1)"],
            ["return", C],
        ],
        5,
    ),
    (
        lambda pt: [  # App is called at transaction index 0
            greeting := pt.ScratchVar(
                pt.TealType.bytes, 20
            ),  # this variable will live in scratch slot 20
            app1_seq := pt.Seq(
                [
                    pt.If(pt.Txn.sender() == pt.App.globalGet(pt.Bytes("creator")))
                    .Then(greeting.store(pt.Bytes("hi creator!")))
                    .Else(greeting.store(pt.Bytes("hi user!"))),
                    pt.Int(1),
                ]
            ),
            greetingFromPreviousApp := pt.ImportScratchValue(
                0, 20
            ),  # loading scratch slot 20 from the transaction at index 0
            app2_seq := pt.Seq(
                [
                    # not shown: make sure that the transaction at index 0 is an app call to App A
                    pt.App.globalPut(
                        pt.Bytes("greeting from prev app"), greetingFromPreviousApp
                    ),
                    pt.Int(1),
                ]
            ),
            pt.And(app1_seq, app2_seq),
        ][-1],
        [
            [P, C],
            ["txn Sender", "pt.Txn.sender()"],
            ['byte "creator"', "pt.Bytes('creator')"],
            ["app_global_get", "pt.App.globalGet(pt.Bytes('creator'))"],
            ["==", "pt.Txn.sender() == pt.App.globalGet(pt.Bytes('creator'))"],
            [
                "bnz main_l2",  # .Then(...) would be a bit better here
                "pt.If(pt.Txn.sender() == pt.App.globalGet(pt.Bytes('creator')))",
            ],
            ['byte "hi user!"', "pt.Bytes('hi user!')"],
            ["store 20", "greeting.store(pt.Bytes('hi user!'))"],
            [
                "b main_l3",  # pt.If(...) does make sense because this is the next scope
                "pt.If(pt.Txn.sender() == pt.App.globalGet(pt.Bytes('creator')))",
            ],
            [
                "main_l2:",  # .Then(...) is a bit better
                "pt.If(pt.Txn.sender() == pt.App.globalGet(pt.Bytes('creator')))",
            ],
            ['byte "hi creator!"', "pt.Bytes('hi creator!')"],
            ["store 20", "greeting.store(pt.Bytes('hi creator!'))"],
            [
                "main_l3:",
                "pt.If(pt.Txn.sender() == pt.App.globalGet(pt.Bytes('creator')))",
            ],  # pt.If(...) etc. sent us over here
            ["int 1", "pt.Int(1)"],
            ['byte "greeting from prev app"', "pt.Bytes('greeting from prev app')"],
            ["gload 0 20", "pt.ImportScratchValue(0, 20)"],
            [
                "app_global_put",
                "pt.App.globalPut(pt.Bytes('greeting from prev app'), greetingFromPreviousApp)",
            ],
            ["int 1", "pt.Int(1)"],
            ["&&", "pt.And(app1_seq, app2_seq)"],
            ["return", C],
        ],
        4,
        "Application",
    ),
    (
        lambda pt: [
            arg := pt.Btoi(pt.Arg(1)),
            pt.If(arg == pt.Int(0))
            .Then(pt.Reject())
            .ElseIf(arg == pt.Int(1))
            .Then(pt.Reject())
            .ElseIf(arg == pt.Int(2))
            .Then(pt.Approve())
            .Else(pt.Reject()),
        ][-1],
        [
            [P, C],
            ("arg 1", "pt.Arg(1)"),
            ("btoi", "pt.Btoi(pt.Arg(1))"),
            ("int 0", "pt.Int(0)"),
            ("==", "arg == pt.Int(0)"),
            ("bnz main_l6", "pt.If(arg == pt.Int(0))"),
            ("arg 1", "pt.Arg(1)"),
            ("btoi", "pt.Btoi(pt.Arg(1))"),
            ("int 1", "pt.Int(1)"),
            ("==", "arg == pt.Int(1)"),
            (
                "bnz main_l5",
                "pt.If(arg == pt.Int(0)).Then(pt.Reject()).ElseIf(arg == pt.Int(1))",
            ),
            ("arg 1", "pt.Arg(1)"),
            ("btoi", "pt.Btoi(pt.Arg(1))"),
            ("int 2", "pt.Int(2)"),
            ("==", "arg == pt.Int(2)"),
            (
                "bnz main_l4",
                "pt.If(arg == pt.Int(0)).Then(pt.Reject()).ElseIf(arg == pt.Int(1)).Then(pt.Reject()).ElseIf(arg == pt.Int(2))",
            ),
            ("int 0", "pt.Reject()"),
            ("return", "pt.Reject()"),
            (
                "main_l4:",
                "pt.If(arg == pt.Int(0)).Then(pt.Reject()).ElseIf(arg == pt.Int(1)).Then(pt.Reject()).ElseIf(arg == pt.Int(2))",
            ),
            ("int 1", "pt.Approve()"),
            ("return", "pt.Approve()"),
            (
                "main_l5:",
                "pt.If(arg == pt.Int(0)).Then(pt.Reject()).ElseIf(arg == pt.Int(1))",
            ),
            ("int 0", "pt.Reject()"),
            ("return", "pt.Reject()"),
            ("main_l6:", "pt.If(arg == pt.Int(0))"),
            ("int 0", "pt.Reject()"),
            ("return", "pt.Reject()"),
        ],
        2,
        "Signature",
    ),
    (
        lambda pt: [
            totalFees := pt.ScratchVar(pt.TealType.uint64),
            i := pt.ScratchVar(pt.TealType.uint64),
            pt.Seq(
                i.store(pt.Int(0)),
                totalFees.store(pt.Int(0)),
                pt.While(i.load() < pt.Global.group_size()).Do(
                    totalFees.store(totalFees.load() + pt.Gtxn[i.load()].fee()),
                    i.store(i.load() + pt.Int(1)),
                ),
                pt.Approve(),
            ),
        ][-1],
        (
            [P, C],
            ("int 0", "pt.Int(0)"),
            ("store 1", "i.store(pt.Int(0))"),
            ("int 0", "pt.Int(0)"),
            ("store 0", "totalFees.store(pt.Int(0))"),
            ("main_l1:", BIG_W),  # yes, this makes sense to be While(...)
            ("load 1", "i.load()"),
            ("global GroupSize", "pt.Global.group_size()"),
            ("<", "i.load() < pt.Global.group_size()"),
            ("bz main_l3", BIG_W),  # yes, this as well cause we're exiting while
            ("load 0", "totalFees.load()"),
            ("load 1", "i.load()"),
            ("gtxns Fee", "pt.Gtxn[i.load()].fee()"),
            ("+", "totalFees.load() + pt.Gtxn[i.load()].fee()"),
            ("store 0", "totalFees.store(totalFees.load() + pt.Gtxn[i.load()].fee())"),
            ("load 1", "i.load()"),
            ("int 1", "pt.Int(1)"),
            ("+", "i.load() + pt.Int(1)"),
            ("store 1", "i.store(i.load() + pt.Int(1))"),
            ("b main_l1", BIG_W),  # but the only reason for this is While(...)
            ("main_l3:", BIG_W),  # and this exit condition as well for the While(...)
            ("int 1", "pt.Approve()"),
            ("return", "pt.Approve()"),
        ),
        3,
    ),
    (
        lambda pt: [
            totalFees := pt.ScratchVar(pt.TealType.uint64),
            i := pt.ScratchVar(pt.TealType.uint64),
            pt.Seq(
                totalFees.store(pt.Int(0)),
                pt.For(
                    i.store(pt.Int(0)),
                    i.load() < pt.Global.group_size(),
                    i.store(i.load() + pt.Int(1)),
                ).Do(totalFees.store(totalFees.load() + pt.Gtxn[i.load()].fee())),
                pt.Approve(),
            ),
        ][-1],
        [
            [P, C],
            ("int 0", "pt.Int(0)"),
            ("store 0", "totalFees.store(pt.Int(0))"),
            ("int 0", "pt.Int(0)"),
            ("store 1", "i.store(pt.Int(0))"),
            ("main_l1:", BIG_F),
            ("load 1", "i.load()"),
            ("global GroupSize", "pt.Global.group_size()"),
            ("<", "i.load() < pt.Global.group_size()"),
            ("bz main_l3", BIG_F),  # .Do(...) seems a bit more appropriate here
            ("load 0", "totalFees.load()"),
            ("load 1", "i.load()"),
            ("gtxns Fee", "pt.Gtxn[i.load()].fee()"),
            ("+", "totalFees.load() + pt.Gtxn[i.load()].fee()"),
            ("store 0", "totalFees.store(totalFees.load() + pt.Gtxn[i.load()].fee())"),
            ("load 1", "i.load()"),
            ("int 1", "pt.Int(1)"),
            ("+", "i.load() + pt.Int(1)"),
            ("store 1", "i.store(i.load() + pt.Int(1))"),
            ("b main_l1", BIG_F),
            ("main_l3:", BIG_F),
            ("int 1", "pt.Approve()"),
            ("return", "pt.Approve()"),
        ],
        3,
    ),
    (
        lambda pt: [
            numPayments := pt.ScratchVar(pt.TealType.uint64),
            i := pt.ScratchVar(pt.TealType.uint64),
            pt.Seq(
                numPayments.store(pt.Int(0)),
                pt.For(
                    i.store(pt.Int(0)),
                    i.load() < pt.Global.group_size(),
                    i.store(i.load() + pt.Int(1)),
                ).Do(
                    pt.If(pt.Gtxn[i.load()].type_enum() != pt.TxnType.Payment)
                    .Then(pt.Continue())
                    .ElseIf(pt.Int(42))
                    .Then(pt.Break()),
                    numPayments.store(numPayments.load() + pt.Int(1)),
                ),
                pt.Approve(),
            ),
        ][-1],
        [
            [P, C],
            ("int 0", "pt.Int(0)"),
            ("store 0", "numPayments.store(pt.Int(0))"),
            ("int 0", "pt.Int(0)"),
            ("store 1", "i.store(pt.Int(0))"),
            (
                "main_l1:",
                "pt.For(i.store(pt.Int(0)), i.load() < pt.Global.group_size(), i.store(i.load() + pt.Int(1)))",
            ),
            ("load 1", "i.load()"),
            ("global GroupSize", "pt.Global.group_size()"),
            ("<", "i.load() < pt.Global.group_size()"),
            (
                "bz main_l6",
                "pt.For(i.store(pt.Int(0)), i.load() < pt.Global.group_size(), i.store(i.load() + pt.Int(1)))",
            ),
            ("load 1", "i.load()"),
            ("gtxns TypeEnum", "pt.Gtxn[i.load()].type_enum()"),
            ("int pay", "pt.Gtxn[i.load()].type_enum() != pt.TxnType.Payment"),
            ("!=", "pt.Gtxn[i.load()].type_enum() != pt.TxnType.Payment"),
            (
                "bnz main_l5",
                "pt.If(pt.Gtxn[i.load()].type_enum() != pt.TxnType.Payment)",  # pt.Continue() is better
            ),
            ("int 42", "pt.Int(42)"),
            (
                "bnz main_l6",
                "pt.If(pt.Gtxn[i.load()].type_enum() != pt.TxnType.Payment).Then(pt.Continue()).ElseIf(pt.Int(42))",  # pt.Break() would be better
            ),
            ("load 0", "numPayments.load()"),
            ("int 1", "pt.Int(1)"),
            ("+", "numPayments.load() + pt.Int(1)"),
            ("store 0", "numPayments.store(numPayments.load() + pt.Int(1))"),
            (
                "main_l5:",
                "pt.If(pt.Gtxn[i.load()].type_enum() != pt.TxnType.Payment)",
            ),
            ("load 1", "i.load()"),
            ("int 1", "pt.Int(1)"),
            ("+", "i.load() + pt.Int(1)"),
            ("store 1", "i.store(i.load() + pt.Int(1))"),
            (
                "b main_l1",
                "pt.If(pt.Gtxn[i.load()].type_enum() != pt.TxnType.Payment).Then(pt.Continue()).ElseIf(pt.Int(42))",  # ???pt.Continue() is better
            ),
            (
                "main_l6:",
                "pt.For(i.store(pt.Int(0)), i.load() < pt.Global.group_size(), i.store(i.load() + pt.Int(1)))",
            ),
            ("int 1", "pt.Approve()"),
            ("return", "pt.Approve()"),
        ],
        3,
    ),
    (
        lambda pt: pt.Seq(
            pt.For(pt.Pop(pt.Int(1)), pt.Int(2), pt.Pop(pt.Int(3))).Do(
                pt.Seq(
                    pt.Cond(
                        [pt.Int(4), pt.Continue()],
                        [pt.Int(5), pt.Break()],
                    ),
                    pt.Pop(pt.Int(6)),
                )
            ),
            pt.Reject(),
        ),
        [
            [P, C],
            ("int 1", "pt.Int(1)"),
            ("pop", "pt.Pop(pt.Int(1))"),
            ("main_l1:", "pt.For(pt.Pop(pt.Int(1)), pt.Int(2), pt.Pop(pt.Int(3)))"),
            ("int 2", "pt.Int(2)"),
            ("bz main_l6", "pt.For(pt.Pop(pt.Int(1)), pt.Int(2), pt.Pop(pt.Int(3)))"),
            ("int 4", "pt.Int(4)"),
            (
                "bnz main_l5",
                "pt.Cond([pt.Int(4), pt.Continue()], [pt.Int(5), pt.Break()])",
            ),
            ("int 5", "pt.Int(5)"),
            (
                "bnz main_l6",
                "pt.Cond([pt.Int(4), pt.Continue()], [pt.Int(5), pt.Break()])",
            ),
            ("err", "pt.Cond([pt.Int(4), pt.Continue()], [pt.Int(5), pt.Break()])"),
            (
                "main_l5:",
                "pt.Cond([pt.Int(4), pt.Continue()], [pt.Int(5), pt.Break()])",
            ),
            ("int 3", "pt.Int(3)"),
            ("pop", "pt.Pop(pt.Int(3))"),
            (
                "b main_l1",
                "pt.Cond([pt.Int(4), pt.Continue()], [pt.Int(5), pt.Break()])",
            ),
            ("main_l6:", "pt.For(pt.Pop(pt.Int(1)), pt.Int(2), pt.Pop(pt.Int(3)))"),
            ("int 0", "pt.Reject()"),
            ("return", "pt.Reject()"),
        ],
    ),
    (
        lambda pt: pt.Seq(
            pt.Pop(pt.Int(0)),
            pt.While(pt.Int(1)).Do(
                pt.Cond(
                    [pt.Int(2), pt.Continue()],
                    [pt.Int(3), pt.Break()],
                    [pt.Int(4), pt.Pop(pt.Int(5))],
                ),
                pt.Pop(pt.Int(6)),
            ),
            pt.Reject(),
        ),
        # This example shows that Continue() and Break() don't receive credit for the labelled targets
        [
            [P, C],
            ("int 0", "pt.Int(0)"),
            ("pop", "pt.Pop(pt.Int(0))"),
            ("main_l1:", "pt.While(pt.Int(1))"),
            ("int 1", "pt.Int(1)"),
            (
                "bz main_l7",
                "pt.While(pt.Int(1))",
            ),  # makes sense as While determines where to branch
            ("int 2", "pt.Int(2)"),
            (
                "bnz main_l1",  # TODO: this could be improved as Continue() ought to get credit here
                "pt.Cond([pt.Int(2), pt.Continue()], [pt.Int(3), pt.Break()], [pt.Int(4), pt.Pop(pt.Int(5))])",
            ),
            ("int 3", "pt.Int(3)"),
            (
                "bnz main_l7",  # TODO: this could be improved as Break() ought to get credit here
                "pt.Cond([pt.Int(2), pt.Continue()], [pt.Int(3), pt.Break()], [pt.Int(4), pt.Pop(pt.Int(5))])",
            ),
            ("int 4", "pt.Int(4)"),
            (
                "bnz main_l6",  # makes sense
                "pt.Cond([pt.Int(2), pt.Continue()], [pt.Int(3), pt.Break()], [pt.Int(4), pt.Pop(pt.Int(5))])",
            ),
            (
                "err",  # makes sense
                "pt.Cond([pt.Int(2), pt.Continue()], [pt.Int(3), pt.Break()], [pt.Int(4), pt.Pop(pt.Int(5))])",
            ),
            (
                "main_l6:",  # makes sense
                "pt.Cond([pt.Int(2), pt.Continue()], [pt.Int(3), pt.Break()], [pt.Int(4), pt.Pop(pt.Int(5))])",
            ),
            ("int 5", "pt.Int(5)"),
            ("pop", "pt.Pop(pt.Int(5))"),
            ("int 6", "pt.Int(6)"),
            ("pop", "pt.Pop(pt.Int(6))"),
            (
                "b main_l1",
                "pt.Cond([pt.Int(2), pt.Continue()], [pt.Int(3), pt.Break()], [pt.Int(4), pt.Pop(pt.Int(5))])",
            ),
            (
                "main_l7:",
                "pt.While(pt.Int(1))",
            ),  # makes sense as this is the exit condition - but it could also have been Break()
            ("int 0", "pt.Reject()"),
            ("return", "pt.Reject()"),
        ],
    ),
]


@pytest.mark.parametrize("i, test_case", enumerate(CONSTRUCTS))
@pytest.mark.parametrize("mode", ["Application", "Signature"])
@pytest.mark.parametrize("version", range(2, 8))
@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_constructs(_, i, test_case, mode, version):
    """
    Sanity check source mapping the most important PyTeal constructs

    Cannot utilize @pytest.mark.parametrize because of monkeypatching
    """
    import pyteal as pt

    # Occationally we stop getting nodes from AST under random conditions
    def unparse(tmis):
        return list(map(lambda tmi: ast.unparse(tmi.node), tmis))

    expr, line2unparsed = test_case[:2]
    line2unparsed = deepcopy(line2unparsed)
    # fill the pragma template:
    line2unparsed[0][0] = line2unparsed[0][0].format(v=version)

    expr = expr(pt)
    if len(test_case) > 2:
        min_version = test_case[2]
        if version < min_version:
            return
    if len(test_case) > 3:
        fixed_mode = test_case[3]
        if mode != fixed_mode:
            return

    mode = getattr(pt.Mode, mode)
    comp = pt.Compilation(
        expr, mode, version=version, assemble_constants=False, optimize=None
    )
    bundle = comp.compile(with_sourcemap=True)
    sourcemap = bundle.sourcemap

    msg = f"[CASE #{i+1}]: {expr=}, {bundle=}"

    assert sourcemap, msg
    assert sourcemap.hybrid is True, msg
    assert sourcemap.source_inference is True, msg

    tmis = sourcemap.as_list()
    expected_lines, unparsed = list(zip(*line2unparsed))

    msg = f"{msg}, {tmis=}"
    assert list(expected_lines) == bundle.lines, msg
    assert list(expected_lines) == sourcemap.compiled_teal_lines, msg
    assert list(unparsed) == unparse(tmis), msg
