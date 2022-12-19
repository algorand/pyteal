"""
This file monkey-patches ConfigParser in order to enable source mapping
and test the results of source mapping various PyTeal apps.
"""

import ast
from configparser import ConfigParser
from copy import deepcopy
from pathlib import Path
import sys
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

    actual_unparsed = [x._hybrid_w_offset() for x in ptsm._cached_tmis]
    assert_algobank_unparsed_as_expected(actual_unparsed)

    r3sm = ptsm._cached_r3sourcemap
    assert r3sm

    assert filename == r3sm.file
    assert cast(str, r3sm.source_root).endswith("/pyteal/")
    assert list(range(len(r3sm.entries))) == [l for l, _ in r3sm.entries]
    assert all(c == 0 for _, c in r3sm.entries)
    assert all(x == (0,) for x in r3sm.index)
    assert len(r3sm.entries) == len(r3sm.index)

    this_file = __file__.split("/")[-1]
    expected_source_files = [
        "examples/application/abi/algobank.py",
        f"tests/unit/{this_file}",
    ]
    assert expected_source_files == r3sm.source_files

    r3sm_json = r3sm.to_json()

    assert "mappings" in r3sm_json

    r3sm_for_version = {
        (
            3,
            11,
        ): "AA2BqB;ACXZ;AAAA;AAAA;AAAA;AA0BT;AAAA;AAAA;AAAA;AAwBA;AAAA;AAAA;AAAA;AAaA;AAAA;AAAA;AAAA;ADpDqB;ACoDrB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADpDqB;AAAA;ACoDrB;AAAA;AAAA;AAbA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADvCqB;AAAA;AAAA;AAAA;AAAA;ACuCrB;AAAA;AAxBA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADfqB;AAAA;ACerB;AAAA;AAAA;AA1BS;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAJL;AACc;AAAd;AAA4C;AAAc;AAA3B;AAA/B;AAFuB;AAKlB;AAAA;AAAA;AAM8B;AAAA;AAN9B;AAAA;AAAA;AAAA;AAAA;AAI6B;AAAA;ADOjB;AAAA;AAAA;ACpBH;AAAgB;AAAhB;AAAP;ADoBU;AAAA;AAAA;AAAA;AAAA;AAAA;AC4BN;AAAA;AAA0B;AAAA;AAA1B;AAAP;AACO;AAAA;AAA4B;AAA5B;AAAP;AAEI;AAAA;AACA;AACa;AAAA;AAAkB;AAA/B;AAAmD;AAAA;AAAnD;AAHJ;AD9Ba;ACuCrB;AAAA;AAAA;AASmC;AAAgB;AAA7B;ADhDD;AAAA;AAAA;AAAA;AAAA;AAAA;ACwET;AACA;AACa;AAAc;AAA3B;AAA+C;AAA/C;AAHJ;AAKA;AACA;AAAA;AAG2B;AAAA;AAH3B;AAIyB;AAJzB;AAKsB;AALtB;AAQA;ADrFa",
        (
            3,
            10,
        ): "AAgBS;AAAA;AAAA;AAAA;AAAA;AA0BT;AAAA;AAAA;AAAA;AAwBA;AAAA;AAAA;AAAA;AAaA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACpDA;AAAA;ADoDA;AAAA;AAAA;AAbA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACvCA;AAAA;AAAA;AAAA;AAAA;ADuCA;AAAA;AAxBA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACfA;AAAA;ADeA;AAAA;AAAA;AA1BS;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAJL;AACc;AAAd;AAA4C;AAAc;AAA3B;AAA/B;AAFuB;AAKlB;AAAA;AAAA;AAM8B;AAAA;AAN9B;AAAA;AAAA;AAAA;AAAA;AAI6B;AAAA;ACOtC;AAAA;AAAA;ADpBkB;AAAgB;AAAhB;AAAP;ACoBX;AAAA;AAAA;AAAA;AAAA;AAAA;AD4Be;AAAA;AAA0B;AAAA;AAA1B;AAAP;AACO;AAAA;AAA4B;AAA5B;AAAP;AAEI;AAAA;AACA;AACa;AAAA;AAAkB;AAA/B;AAAmD;AAAA;AAAnD;AAHJ;AC9BR;ADuCA;AAAA;AAAA;AASmC;AAAgB;AAA7B;AChDtB;AAAA;AAAA;AAAA;AAAA;AAAA;ADwEY;AACA;AACa;AAAc;AAA3B;AAA+C;AAA/C;AAHJ;AAKA;AACA;AAAA;AAG2B;AAAA;AAH3B;AAIyB;AAJzB;AAKsB;AALtB;AAQA;AAAA",
    }

    py_version = sys.version_info[:2]
    if py_version >= (3, 11):
        assert r3sm_for_version[(3, 11)] == r3sm_json["mappings"]
    else:
        # allow for 3.10 to be flaky
        if r3sm_for_version[(3, 11)] != r3sm_json["mappings"]:
            assert r3sm_for_version[(3, 10)] == r3sm_json["mappings"]

    assert "file" in r3sm_json
    assert filename == r3sm_json["file"]

    assert "sources" in r3sm_json

    # jsonizing creates it's own separate order based on first seen and defaultdict with autoindex
    expected_json_source_files = [
        f"tests/unit/{this_file}",
        "examples/application/abi/algobank.py",
    ]
    assert set(expected_json_source_files) == set(r3sm_json["sources"])

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

    with open(ALGOBANK / "algobank_approval.teal", "r") as af:
        assert af.read() == compile_bundle.approval_sourcemap.pure_teal()

    with open(ALGOBANK / "algobank_clear_state.teal", "r") as cf:
        assert cf.read() == compile_bundle.clear_sourcemap.pure_teal()


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_mocked_config_for_frames(_):
    config = ConfigParser()
    assert config.getboolean("pyteal-source-mapper", "enabled") is True
    from pyteal.stack_frame import Frames

    assert Frames.sourcemapping_is_off() is False
    assert Frames.sourcemapping_is_off(_force_refresh=True) is False


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
BIG_A2 = "pt.And(pt.Int(1) - pt.Int(2), pt.Not(pt.Int(3)), pt.Int(4) ^ pt.Int(5), ~pt.Int(6), pt.BytesEq(pt.Bytes('7'), pt.Bytes('8')), pt.GetBit(pt.Int(9), pt.Int(10)), pt.SetBit(pt.Int(11), pt.Int(12), pt.Int(13)), pt.GetByte(pt.Bytes('14'), pt.Int(15)), pt.Btoi(pt.Concat(pt.BytesDiv(pt.Bytes('101'), pt.Bytes('102')), pt.BytesNot(pt.Bytes('103')), pt.BytesZero(pt.Int(10)), pt.SetBit(pt.Bytes('105'), pt.Int(106), pt.Int(107)), pt.SetByte(pt.Bytes('108'), pt.Int(109), pt.Int(110)))))"
BIG_C2 = "pt.Concat(pt.BytesDiv(pt.Bytes('101'), pt.Bytes('102')), pt.BytesNot(pt.Bytes('103')), pt.BytesZero(pt.Int(10)), pt.SetBit(pt.Bytes('105'), pt.Int(106), pt.Int(107)), pt.SetByte(pt.Bytes('108'), pt.Int(109), pt.Int(110)))"

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
    (  # 17
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
            ("bnz main_l18", "pt.Txn.application_id() == pt.Int(0)"),
            ("txn OnCompletion", "pt.Txn.on_completion()"),
            (
                "int DeleteApplication",
                "pt.Txn.on_completion() == pt.OnComplete.DeleteApplication",
            ),  # source inferencing at work here!!!!
            ("==", "pt.Txn.on_completion() == pt.OnComplete.DeleteApplication"),
            (
                "bnz main_l17",
                "pt.Txn.on_completion() == pt.OnComplete.DeleteApplication",
            ),
            ("txn OnCompletion", "pt.Txn.on_completion()"),
            (
                "int UpdateApplication",
                "pt.Txn.on_completion() == pt.OnComplete.UpdateApplication",
            ),  # source inferencing
            ("==", "pt.Txn.on_completion() == pt.OnComplete.UpdateApplication"),
            (
                "bnz main_l16",
                "pt.Txn.on_completion() == pt.OnComplete.UpdateApplication",
            ),  # yep
            ("txn OnCompletion", "pt.Txn.on_completion()"),
            ("int CloseOut", "pt.Txn.on_completion() == pt.OnComplete.CloseOut"),
            ("==", "pt.Txn.on_completion() == pt.OnComplete.CloseOut"),
            ("bnz main_l15", "pt.Txn.on_completion() == pt.OnComplete.CloseOut"),
            ("txn OnCompletion", "pt.Txn.on_completion()"),
            ("int OptIn", "pt.Txn.on_completion() == pt.OnComplete.OptIn"),
            ("==", "pt.Txn.on_completion() == pt.OnComplete.OptIn"),
            ("bnz main_l14", "pt.Txn.on_completion() == pt.OnComplete.OptIn"),
            ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
            ('byte "set admin"', "pt.Bytes('set admin')"),
            ("==", "pt.Txn.application_args[0] == pt.Bytes('set admin')"),
            ("bnz main_l13", "pt.Txn.application_args[0] == pt.Bytes('set admin')"),
            ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
            ('byte "mint"', "pt.Bytes('mint')"),
            ("==", "pt.Txn.application_args[0] == pt.Bytes('mint')"),
            ("bnz main_l12", "pt.Txn.application_args[0] == pt.Bytes('mint')"),
            ("txna ApplicationArgs 0", "pt.Txn.application_args[0]"),
            ('byte "transfer"', "pt.Bytes('transfer')"),
            ("==", "pt.Txn.application_args[0] == pt.Bytes('transfer')"),
            ("bnz main_l11", "pt.Txn.application_args[0] == pt.Bytes('transfer')"),
            ("txna Accounts 4", "pt.Txn.accounts[4]"),
            ('byte "foo"', "pt.Bytes('foo')"),
            ("==", "pt.Txn.accounts[4] == pt.Bytes('foo')"),
            ("bnz main_l10", "pt.Txn.accounts[4] == pt.Bytes('foo')"),
            ("err", BIG_C),
            ("main_l10:", "pt.Txn.accounts[4] == pt.Bytes('foo')"),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l11:", "pt.Txn.application_args[0] == pt.Bytes('transfer')"),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l12:", "pt.Txn.application_args[0] == pt.Bytes('mint')"),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l13:", "pt.Txn.application_args[0] == pt.Bytes('set admin')"),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l14:", "pt.Txn.on_completion() == pt.OnComplete.OptIn"),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l15:", "pt.Txn.on_completion() == pt.OnComplete.CloseOut"),
            ("int 1", "pt.Int(1)"),
            ("return", "pt.Return(pt.Int(1))"),
            ("main_l16:", "pt.Txn.on_completion() == pt.OnComplete.UpdateApplication"),
            ("int 0", "pt.Int(0)"),
            ('byte "admin"', "pt.Bytes('admin')"),
            ("app_local_get", "pt.App.localGet(pt.Int(0), pt.Bytes('admin'))"),
            ("return", "pt.Return(is_admin)"),
            ("main_l17:", "pt.Txn.on_completion() == pt.OnComplete.DeleteApplication"),
            ("int 0", "pt.Int(0)"),
            ('byte "admin"', "pt.Bytes('admin')"),
            ("app_local_get", "pt.App.localGet(pt.Int(0), pt.Bytes('admin'))"),
            ("return", "pt.Return(is_admin)"),
            ("main_l18:", "pt.Txn.application_id() == pt.Int(0)"),
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
    (  # 20
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
            (
                "store 1",
                "pt.App.localGetEx(pt.Int(1), pt.App.id(), pt.Bytes('max balance'))",
            ),
            (
                "store 0",
                "pt.App.localGetEx(pt.Int(1), pt.App.id(), pt.Bytes('max balance'))",
            ),
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
    (  # 22
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
    (  # 24
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
                "bnz main_l2",
                "pt.If(pt.Txn.sender() == pt.App.globalGet(pt.Bytes('creator')))",
            ],
            ['byte "hi user!"', "pt.Bytes('hi user!')"],
            ["store 20", "greeting.store(pt.Bytes('hi user!'))"],
            [
                "b main_l3",
                "pt.If(pt.Txn.sender() == pt.App.globalGet(pt.Bytes('creator')))",
            ],
            [
                "main_l2:",
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
    (  # 25
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
            ("bnz main_l5", "arg == pt.Int(1)"),
            ("arg 1", "pt.Arg(1)"),
            ("btoi", "pt.Btoi(pt.Arg(1))"),
            ("int 2", "pt.Int(2)"),
            ("==", "arg == pt.Int(2)"),
            ("bnz main_l4", "arg == pt.Int(2)"),
            ("int 0", "pt.Reject()"),
            ("return", "pt.Reject()"),
            ("main_l4:", "arg == pt.Int(2)"),
            ("int 1", "pt.Approve()"),
            ("return", "pt.Approve()"),
            ("main_l5:", "arg == pt.Int(1)"),
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
    (  # 28
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
                "pt.For(i.store(pt.Int(0)), i.load() < pt.Global.group_size(), i.store(i.load() + pt.Int(1)))",
            ),
            ("load 1", "i.load()"),
            ("int 1", "pt.Int(1)"),
            ("+", "i.load() + pt.Int(1)"),
            ("store 1", "i.store(i.load() + pt.Int(1))"),
            (
                "b main_l1",
                "pt.For(i.store(pt.Int(0)), i.load() < pt.Global.group_size(), i.store(i.load() + pt.Int(1)))",
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
    (  # 29
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
                "pt.Int(4)",
            ),
            ("int 5", "pt.Int(5)"),
            (
                "bnz main_l6",
                "pt.Int(5)",
            ),
            ("err", "pt.Cond([pt.Int(4), pt.Continue()], [pt.Int(5), pt.Break()])"),
            (
                "main_l5:",
                "pt.For(pt.Pop(pt.Int(1)), pt.Int(2), pt.Pop(pt.Int(3)))",  # Continue would be better
            ),
            ("int 3", "pt.Int(3)"),
            ("pop", "pt.Pop(pt.Int(3))"),
            (
                "b main_l1",
                "pt.For(pt.Pop(pt.Int(1)), pt.Int(2), pt.Pop(pt.Int(3)))",
            ),
            ("main_l6:", "pt.For(pt.Pop(pt.Int(1)), pt.Int(2), pt.Pop(pt.Int(3)))"),
            ("int 0", "pt.Reject()"),
            ("return", "pt.Reject()"),
        ],
    ),
    (  # 30
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
                "pt.Int(2)",
            ),
            ("int 3", "pt.Int(3)"),
            (
                "bnz main_l7",  # TODO: this could be improved as Break() ought to get credit here
                "pt.Int(3)",
            ),
            ("int 4", "pt.Int(4)"),
            (
                "bnz main_l6",  # makes sense
                "pt.Int(4)",
            ),
            (
                "err",  # makes sense
                "pt.Cond([pt.Int(2), pt.Continue()], [pt.Int(3), pt.Break()], [pt.Int(4), pt.Pop(pt.Int(5))])",
            ),
            (
                "main_l6:",  # makes sense
                "pt.While(pt.Int(1))",
            ),
            ("int 5", "pt.Int(5)"),
            ("pop", "pt.Pop(pt.Int(5))"),
            ("int 6", "pt.Int(6)"),
            ("pop", "pt.Pop(pt.Int(6))"),
            (
                "b main_l1",
                "pt.While(pt.Int(1))",
            ),
            (
                "main_l7:",
                "pt.While(pt.Int(1))",
            ),  # makes sense as this is the exit condition - but it could also have been Break()
            ("int 0", "pt.Reject()"),
            ("return", "pt.Reject()"),
        ],
    ),
    (  # 31
        lambda pt: pt.Seq(
            foo := pt.App.globalGetEx(pt.Txn.applications[0], pt.Bytes("flo")),
            pt.Assert(
                pt.Txn.sender() == pt.App.globalGet(pt.Bytes("alice")),
                pt.App.globalGet(pt.Bytes("bob")) != pt.Int(0),
                pt.App.globalGet(pt.Bytes("chiro")) == pt.Bytes("danillo"),
                pt.Global.latest_timestamp() > pt.App.globalGet(pt.Bytes("enya")),
                foo.hasValue(),
            ),
            pt.Int(42),
        ),
        [
            [P, C],
            ("txna Applications 0", "pt.Txn.applications[0]"),
            ('byte "flo"', "pt.Bytes('flo')"),
            (
                "app_global_get_ex",
                "pt.App.globalGetEx(pt.Txn.applications[0], pt.Bytes('flo'))",
            ),
            ("store 1", "pt.App.globalGetEx(pt.Txn.applications[0], pt.Bytes('flo'))"),
            ("store 0", "pt.App.globalGetEx(pt.Txn.applications[0], pt.Bytes('flo'))"),
            ("txn Sender", "pt.Txn.sender()"),
            ('byte "alice"', "pt.Bytes('alice')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('alice'))"),
            ("==", "pt.Txn.sender() == pt.App.globalGet(pt.Bytes('alice'))"),
            ("assert", "pt.Txn.sender() == pt.App.globalGet(pt.Bytes('alice'))"),
            ('byte "bob"', "pt.Bytes('bob')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('bob'))"),
            ("int 0", "pt.Int(0)"),
            ("!=", "pt.App.globalGet(pt.Bytes('bob')) != pt.Int(0)"),
            ("assert", "pt.App.globalGet(pt.Bytes('bob')) != pt.Int(0)"),
            ('byte "chiro"', "pt.Bytes('chiro')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('chiro'))"),
            ('byte "danillo"', "pt.Bytes('danillo')"),
            ("==", "pt.App.globalGet(pt.Bytes('chiro')) == pt.Bytes('danillo')"),
            ("assert", "pt.App.globalGet(pt.Bytes('chiro')) == pt.Bytes('danillo')"),
            ("global LatestTimestamp", "pt.Global.latest_timestamp()"),
            ('byte "enya"', "pt.Bytes('enya')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('enya'))"),
            (">", "pt.Global.latest_timestamp() > pt.App.globalGet(pt.Bytes('enya'))"),
            (
                "assert",
                "pt.Global.latest_timestamp() > pt.App.globalGet(pt.Bytes('enya'))",
            ),
            ("load 1", "foo.hasValue()"),
            ("assert", "foo.hasValue()"),
            ("int 42", "pt.Int(42)"),
            ("return", C),
        ],
        3,
        "Application",
    ),
    (  # 32 - arithmetic
        lambda pt: pt.And(
            pt.Int(1) - pt.Int(2),
            pt.Not(pt.Int(3)),
            pt.Int(4) ^ pt.Int(5),
            ~pt.Int(6),
            pt.BytesEq(pt.Bytes("7"), pt.Bytes("8")),
            pt.GetBit(pt.Int(9), pt.Int(10)),
            pt.SetBit(pt.Int(11), pt.Int(12), pt.Int(13)),
            pt.GetByte(pt.Bytes("14"), pt.Int(15)),
            pt.Btoi(
                pt.Concat(
                    pt.BytesDiv(pt.Bytes("101"), pt.Bytes("102")),
                    pt.BytesNot(pt.Bytes("103")),
                    pt.BytesZero(pt.Int(10)),
                    pt.SetBit(pt.Bytes("105"), pt.Int(106), pt.Int(107)),
                    pt.SetByte(pt.Bytes("108"), pt.Int(109), pt.Int(110)),
                )
            ),
        ),
        [
            [P, C],
            ("int 1", "pt.Int(1)"),
            ("int 2", "pt.Int(2)"),
            ("-", "pt.Int(1) - pt.Int(2)"),
            ("int 3", "pt.Int(3)"),
            ("!", "pt.Not(pt.Int(3))"),
            ("&&", BIG_A2),
            ("int 4", "pt.Int(4)"),
            ("int 5", "pt.Int(5)"),
            ("^", "pt.Int(4) ^ pt.Int(5)"),
            ("&&", BIG_A2),
            ("int 6", "pt.Int(6)"),
            ("~", "~pt.Int(6)"),
            ("&&", BIG_A2),
            ('byte "7"', "pt.Bytes('7')"),
            ('byte "8"', "pt.Bytes('8')"),
            ("b==", "pt.BytesEq(pt.Bytes('7'), pt.Bytes('8'))"),
            ("&&", BIG_A2),
            ("int 9", "pt.Int(9)"),
            ("int 10", "pt.Int(10)"),
            ("getbit", "pt.GetBit(pt.Int(9), pt.Int(10))"),
            ("&&", BIG_A2),
            ("int 11", "pt.Int(11)"),
            ("int 12", "pt.Int(12)"),
            ("int 13", "pt.Int(13)"),
            ("setbit", "pt.SetBit(pt.Int(11), pt.Int(12), pt.Int(13))"),
            ("&&", BIG_A2),
            ('byte "14"', "pt.Bytes('14')"),
            ("int 15", "pt.Int(15)"),
            ("getbyte", "pt.GetByte(pt.Bytes('14'), pt.Int(15))"),
            ("&&", BIG_A2),
            ('byte "101"', "pt.Bytes('101')"),
            ('byte "102"', "pt.Bytes('102')"),
            ("b/", "pt.BytesDiv(pt.Bytes('101'), pt.Bytes('102'))"),
            ('byte "103"', "pt.Bytes('103')"),
            ("b~", "pt.BytesNot(pt.Bytes('103'))"),
            ("concat", BIG_C2),
            ("int 10", "pt.Int(10)"),
            ("bzero", "pt.BytesZero(pt.Int(10))"),
            ("concat", BIG_C2),
            ('byte "105"', "pt.Bytes('105')"),
            ("int 106", "pt.Int(106)"),
            ("int 107", "pt.Int(107)"),
            ("setbit", "pt.SetBit(pt.Bytes('105'), pt.Int(106), pt.Int(107))"),
            ("concat", BIG_C2),
            ('byte "108"', "pt.Bytes('108')"),
            ("int 109", "pt.Int(109)"),
            ("int 110", "pt.Int(110)"),
            ("setbyte", "pt.SetByte(pt.Bytes('108'), pt.Int(109), pt.Int(110))"),
            ("concat", BIG_C2),
            ("btoi", f"pt.Btoi({BIG_C2})"),
            ("&&", BIG_A2),
            ("return", C),
        ],
        4,
    ),
]


@pytest.mark.parametrize("i, test_case", enumerate(CONSTRUCTS))
@pytest.mark.parametrize("mode", ["Application", "Signature"])
@pytest.mark.parametrize("version", range(2, 9))
@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_constructs(_, i, test_case, mode, version):
    """
                                        Sanity check source mapping the most important PyTeal constructs

                            ................FFF.F......

                                        PERFORMANCE RESULTS 10Nov2022 AS ATTEMPT TO STREAMLINE THE SOURCE MAPPER.

                                        TEST COMMAND:
                                        > command gtime -v pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs

                                        FIRST RUN - BEFORE ANY REFACTORING
                                ❯ command gtime -v pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs
                                ======================================================================================================= test session starts =======================================================================================================
                                platform darwin -- Python 3.10.4, pytest-7.1.2, pluggy-1.0.0
                                rootdir: /Users/zeph/github/tzaffi/pyteal
                                plugins: xdist-2.5.0, forked-1.4.0, timeout-2.1.0, memray-1.3.0, cov-3.0.0
                                collected 372 items

                                tests/unit/sourcemap_monkey_unit_test.py .................................................................................................................................................................................. [ 47%]
                                .................................................................................................................................................................................................


                                ========================================================================================================== MEMRAY REPORT ==========================================================================================================
                                Allocations results for tests/unit/sourcemap_monkey_unit_test.py::test_constructs[2-Application-0-test_case0]

                                         📦 Total memory allocated: 28.9MiB
                                         📏 Total allocations: 435609
                                         📊 Histogram of allocation sizes: |  ▃ █    |
                                         🥇 Biggest allocating functions:
                                                - parse:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/ast.py:50 -> 11.0MiB
                                                - <module>:/Users/zeph/github/tzaffi/pyteal/py310ptt/lib/python3.10/site-packages/pycparser/yacctab.py:16 -> 1.5MiB
                                                - updatecache:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/linecache.py:137 -> 1.1MiB
                                                - updatecache:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/linecache.py:137 -> 1.0MiB
                                                - _call_with_frames_removed:<frozen importlib._bootstrap>:241 -> 1.0MiB
                                . . .

                                ======================================================================================================== slowest durations ========================================================================================================
                                58.47s call     tests/unit/sourcemap_monkey_unit_test.py::test_constructs[2-Application-20-test_case20]
                                43.22s call     tests/unit/sourcemap_monkey_unit_test.py::test_constructs[2-Application-18-test_case18]
                                42.10s call     tests/unit/sourcemap_monkey_unit_test.py::test_constructs[2-Application-28-test_case28]

                                . . .


                                (744 durations < 0.005s hidden.  Use -vv to show these durations.)
                                ================================================================================================= 372 passed in 537.85s (0:08:57) =================================================================================================
                                        Command being timed: "pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs"
                                        User time (seconds): 515.76
                                        System time (seconds): 11.91
                                        Percent of CPU this job got: 97%
                                        Elapsed (wall clock) time (h:mm:ss or m:ss): 8:58.53
                                        Average shared text size (kbytes): 0
                                        Average unshared data size (kbytes): 0
                                        Average stack size (kbytes): 0
                                        Average total size (kbytes): 0
                                        Maximum resident set size (kbytes): 102644
                                        Average resident set size (kbytes): 0
                                        Major (requiring I/O) page faults: 66187
                                        Minor (reclaiming a frame) page faults: 215076
                                        Voluntary context switches: 189
                                        Involuntary context switches: 268839
                                        Swaps: 0
                                        File system inputs: 0
                                        File system outputs: 0
                                        Socket messages sent: 0
                                        Socket messages received: 0



                        (741 durations < 0.005s hidden.  Use -vv to show these durations.)
                        ================================================================================================= 372 passed in 545.95s (0:09:05) =================================================================================================
                                Command being timed: "pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs"
                                User time (seconds): 507.70

                        SECOND RUN - just use a regex to match instead of iterating over list

                        ABOUT 5% faster

                    (742 durations < 0.005s hidden.  Use -vv to show these durations.)
                    ================================================================================================= 372 passed in 498.47s (0:08:18) =================================================================================================
                            Command being timed: "pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs"
                            User time (seconds): 482.87

                        THIRD RUN - can we keep only the most relevant `Frames` ?

                3A: just extracted a new method _original_initializer()... don't expect much if any degredation

                3B: more extractions... getting 20% slower...

                3C: post new SUPPOSEDELY faster method - not really, but 25% less memory used

                ❯ command gtime -v pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs
        ======================================================================================================= test session starts =======================================================================================================
        platform darwin -- Python 3.10.4, pytest-7.1.2, pluggy-1.0.0
        rootdir: /Users/zeph/github/tzaffi/pyteal
        plugins: xdist-2.5.0, forked-1.4.0, timeout-2.1.0, memray-1.3.0, cov-3.0.0
        collected 372 items

        tests/unit/sourcemap_monkey_unit_test.py .................................................................................................................................................................................. [ 47%]
        ..................................................................................................................................................................................................                          [100%]


        ========================================================================================================== MEMRAY REPORT ==========================================================================================================
        Allocations results for tests/unit/sourcemap_monkey_unit_test.py::test_constructs[2-Application-0-test_case0]

                 📦 Total memory allocated: 16.9MiB
                 📏 Total allocations: 398334
                 📊 Histogram of allocation sizes: |    █    |
                 🥇 Biggest allocating functions:
                        - parse:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/ast.py:50 -> 3.0MiB
                        - updatecache:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/linecache.py:137 -> 1.1MiB
                        - updatecache:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/linecache.py:137 -> 1.0MiB
                        - _compile_bytecode:<frozen importlib._bootstrap_external>:672 -> 1.0MiB
                        - _compile_bytecode:<frozen importlib._bootstrap_external>:672 -> 1.0MiB



        (742 durations < 0.005s hidden.  Use -vv to show these durations.)
        ================================================================================================= 372 passed in 516.01s (0:08:36) =================================================================================================
                Command being timed: "pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs"
                User time (seconds): 494.42
                System time (seconds): 11.48
                Percent of CPU this job got: 97%

        3D: inline the initializer

        4 - try upgrading to python 3.11:

    ❯ command gtime -v pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs
    ======================================================================================================= test session starts =======================================================================================================
    platform darwin -- Python 3.11.0, pytest-7.1.2, pluggy-1.0.0
    rootdir: /Users/zeph/github/tzaffi/pyteal
    plugins: xdist-2.5.0, forked-1.4.0, timeout-2.1.0, memray-1.3.0, cov-3.0.0
    collected 372 items

    tests/unit/sourcemap_monkey_unit_test.py .................................................................................................................................................................................. [ 47%]
    ..................................................................................................................................................................................................                          [100%]


    ========================================================================================================== MEMRAY REPORT ==========================================================================================================
    Allocations results for tests/unit/sourcemap_monkey_unit_test.py::test_constructs[2-Application-0-test_case0]

             📦 Total memory allocated: 22.9MiB
             📏 Total allocations: 86866
             📊 Histogram of allocation sizes: |    █    |
             🥇 Biggest allocating functions:
                    - _call_with_frames_removed:<frozen importlib._bootstrap>:241 -> 2.7MiB
                    - parse:/Users/zeph/.asdf/installs/python/3.11.0/lib/python3.11/ast.py:50 -> 2.1MiB
                    - updatecache:/Users/zeph/.asdf/installs/python/3.11.0/lib/python3.11/linecache.py:137 -> 2.1MiB
                    - updatecache:/Users/zeph/.asdf/installs/python/3.11.0/lib/python3.11/linecache.py:137 -> 1.0MiB
                    - _compile_bytecode:<frozen importlib._bootstrap_external>:729 -> 1.0MiB


    (744 durations < 0.005s hidden.  Use -vv to show these durations.)
    ====================================================================================================== 372 passed in 38.20s =======================================================================================================
            Command being timed: "pytest --memray --durations=0 tests/unit/sourcemap_monkey_unit_test.py::test_constructs"
            User time (seconds): 27.61
            System time (seconds): 8.61


    """
    import pyteal as pt

    # Occatsionally we stop getting nodes from AST under random conditions
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
    assert sourcemap._hybrid is True, msg
    assert sourcemap._source_inference is True, msg

    tmis = sourcemap.as_list()
    expected_chunks, unparsed = list(zip(*line2unparsed))

    msg = f"{msg}, {tmis=}"
    assert list(expected_chunks) == bundle.teal_chunks, msg
    assert list(expected_chunks) == sourcemap.teal_chunks, msg
    assert list(unparsed) == unparse(tmis), msg


def assert_algobank_unparsed_as_expected(actual):
    expected = [
        (
            0,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            1,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            2,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            3,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            4,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            5,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            6,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            7,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            8,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            9,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            10,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            11,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            12,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            13,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            14,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            15,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            16,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            17,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            18,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            19,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            20,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            21,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            22,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            23,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            24,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            25,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            26,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            27,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            28,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            29,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            30,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            31,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            32,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            33,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            34,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            35,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            36,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            37,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            38,
            {
                (3, 11): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            39,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            40,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            41,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            42,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            43,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            44,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            45,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            46,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            47,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            48,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            49,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            50,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            51,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            52,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            53,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            54,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            55,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            56,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            57,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            58,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            59,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            60,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            61,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            62,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            63,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            64,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            65,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            66,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            67,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            68,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            69,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            70,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            71,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            72,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            73,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            74,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            75,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            76,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            77,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            78,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            79,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            80,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            81,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            82,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            83,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            84,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            85,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            86,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            87,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            88,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            89,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            90,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            91,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            92,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            93,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            94,
            {
                (3, 11): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                    1,
                ),
            },
        ),
        (
            95,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            96,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            97,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            98,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            99,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            100,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            101,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            102,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            103,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            104,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            105,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            106,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            107,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            108,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            109,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            110,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            111,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            112,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            113,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            114,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            115,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            116,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            117,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            118,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            119,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            120,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            121,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            122,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            123,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            124,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            125,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            126,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            127,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            128,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            129,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            130,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            131,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            132,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            133,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            134,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            135,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            136,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            137,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (138, {(3, 11): ("Bytes('lost')", 0), (3, 10): ("Bytes('lost')", 0)}),
        (139, {(3, 11): ("Bytes('lost')", 0), (3, 10): ("Bytes('lost')", 0)}),
        (
            140,
            {
                (3, 11): ("App.globalGet(Bytes('lost'))", 0),
                (3, 10): ("App.globalGet(Bytes('lost'))", 0),
            },
        ),
        (141, {(3, 11): ("Txn.sender()", 0), (3, 10): ("Txn.sender()", 0)}),
        (142, {(3, 11): ("Bytes('balance')", 0), (3, 10): ("Bytes('balance')", 0)}),
        (
            143,
            {
                (3, 11): ("App.localGet(Txn.sender(), Bytes('balance'))", 0),
                (3, 10): ("App.localGet(Txn.sender(), Bytes('balance'))", 0),
            },
        ),
        (
            144,
            {
                (3, 11): (
                    "App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance'))",
                    0,
                ),
                (3, 10): (
                    "App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance'))",
                    0,
                ),
            },
        ),
        (
            145,
            {
                (3, 11): (
                    "App.globalPut(Bytes('lost'), App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance')))",
                    0,
                ),
                (3, 10): (
                    "App.globalPut(Bytes('lost'), App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance')))",
                    0,
                ),
            },
        ),
        (
            146,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            147,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            148,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (149, {(3, 11): ("Approve()", 0), (3, 10): ("Approve()", 0)}),
        (150, {(3, 11): ("Approve()", 0), (3, 10): ("Approve()", 0)}),
        (
            151,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            152,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            153,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            154,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (
            155,
            {
                (3, 11): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
                (3, 10): (
                    "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))",
                    0,
                ),
            },
        ),
        (156, {(3, 11): ("Approve()", 0), (3, 10): ("Approve()", 0)}),
        (157, {(3, 11): ("Approve()", 0), (3, 10): ("Approve()", 0)}),
        (
            158,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            159,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            160,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (161, {(3, 11): ("Txn.sender()", 0), (3, 10): ("Txn.sender()", 0)}),
        (
            162,
            {
                (3, 11): ("Global.creator_address()", 0),
                (3, 10): ("Global.creator_address()", 0),
            },
        ),
        (
            163,
            {
                (3, 11): ("Txn.sender() == Global.creator_address()", 0),
                (3, 10): ("Txn.sender() == Global.creator_address()", 0),
            },
        ),
        (
            164,
            {
                (3, 11): ("Assert(Txn.sender() == Global.creator_address())", 0),
                (3, 10): ("Assert(Txn.sender() == Global.creator_address())", 0),
            },
        ),
        (
            165,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            166,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            167,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            168,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            169,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            170,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (171, {(3, 11): ("payment.get()", 0), (3, 10): ("payment.get()", 0)}),
        (
            172,
            {
                (3, 11): ("payment.get().sender()", 0),
                (3, 10): ("payment.get().sender()", 0),
            },
        ),
        (173, {(3, 11): ("sender.address()", 0), (3, 10): ("sender.address()", 0)}),
        (174, {(3, 11): ("sender.address()", 0), (3, 10): ("sender.address()", 0)}),
        (
            175,
            {
                (3, 11): ("payment.get().sender() == sender.address()", 0),
                (3, 10): ("payment.get().sender() == sender.address()", 0),
            },
        ),
        (
            176,
            {
                (3, 11): ("Assert(payment.get().sender() == sender.address())", 0),
                (3, 10): ("Assert(payment.get().sender() == sender.address())", 0),
            },
        ),
        (177, {(3, 11): ("payment.get()", 0), (3, 10): ("payment.get()", 0)}),
        (
            178,
            {
                (3, 11): ("payment.get().receiver()", 0),
                (3, 10): ("payment.get().receiver()", 0),
            },
        ),
        (
            179,
            {
                (3, 11): ("Global.current_application_address()", 0),
                (3, 10): ("Global.current_application_address()", 0),
            },
        ),
        (
            180,
            {
                (3, 11): (
                    "payment.get().receiver() == Global.current_application_address()",
                    0,
                ),
                (3, 10): (
                    "payment.get().receiver() == Global.current_application_address()",
                    0,
                ),
            },
        ),
        (
            181,
            {
                (3, 11): (
                    "Assert(payment.get().receiver() == Global.current_application_address())",
                    0,
                ),
                (3, 10): (
                    "Assert(payment.get().receiver() == Global.current_application_address())",
                    0,
                ),
            },
        ),
        (182, {(3, 11): ("sender.address()", 0), (3, 10): ("sender.address()", 0)}),
        (183, {(3, 11): ("sender.address()", 0), (3, 10): ("sender.address()", 0)}),
        (184, {(3, 11): ("Bytes('balance')", 0), (3, 10): ("Bytes('balance')", 0)}),
        (185, {(3, 11): ("sender.address()", 0), (3, 10): ("sender.address()", 0)}),
        (186, {(3, 11): ("sender.address()", 0), (3, 10): ("sender.address()", 0)}),
        (187, {(3, 11): ("Bytes('balance')", 0), (3, 10): ("Bytes('balance')", 0)}),
        (
            188,
            {
                (3, 11): ("App.localGet(sender.address(), Bytes('balance'))", 0),
                (3, 10): ("App.localGet(sender.address(), Bytes('balance'))", 0),
            },
        ),
        (189, {(3, 11): ("payment.get()", 0), (3, 10): ("payment.get()", 0)}),
        (
            190,
            {
                (3, 11): ("payment.get().amount()", 0),
                (3, 10): ("payment.get().amount()", 0),
            },
        ),
        (
            191,
            {
                (3, 11): (
                    "App.localGet(sender.address(), Bytes('balance')) + payment.get().amount()",
                    0,
                ),
                (3, 10): (
                    "App.localGet(sender.address(), Bytes('balance')) + payment.get().amount()",
                    0,
                ),
            },
        ),
        (
            192,
            {
                (3, 11): (
                    "App.localPut(sender.address(), Bytes('balance'), App.localGet(sender.address(), Bytes('balance')) + payment.get().amount())",
                    0,
                ),
                (3, 10): (
                    "App.localPut(sender.address(), Bytes('balance'), App.localGet(sender.address(), Bytes('balance')) + payment.get().amount())",
                    0,
                ),
            },
        ),
        (
            193,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            194,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            195,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (
            196,
            {
                (3, 11): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
                (3, 10): (
                    "def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:",
                    1,
                ),
            },
        ),
        (197, {(3, 11): ("user.address()", 0), (3, 10): ("user.address()", 0)}),
        (198, {(3, 11): ("Bytes('balance')", 0), (3, 10): ("Bytes('balance')", 0)}),
        (
            199,
            {
                (3, 11): ("App.localGet(user.address(), Bytes('balance'))", 0),
                (3, 10): ("App.localGet(user.address(), Bytes('balance'))", 0),
            },
        ),
        (
            200,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            201,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            202,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            203,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            204,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (
            205,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("compile_bundle = router.compile(", 0),
            },
        ),
        (206, {(3, 11): ("Txn.sender()", 0), (3, 10): ("Txn.sender()", 0)}),
        (207, {(3, 11): ("Bytes('balance')", 0), (3, 10): ("Bytes('balance')", 0)}),
        (208, {(3, 11): ("Txn.sender()", 0), (3, 10): ("Txn.sender()", 0)}),
        (209, {(3, 11): ("Bytes('balance')", 0), (3, 10): ("Bytes('balance')", 0)}),
        (
            210,
            {
                (3, 11): ("App.localGet(Txn.sender(), Bytes('balance'))", 0),
                (3, 10): ("App.localGet(Txn.sender(), Bytes('balance'))", 0),
            },
        ),
        (211, {(3, 11): ("amount.get()", 0), (3, 10): ("amount.get()", 0)}),
        (
            212,
            {
                (3, 11): (
                    "App.localGet(Txn.sender(), Bytes('balance')) - amount.get()",
                    0,
                ),
                (3, 10): (
                    "App.localGet(Txn.sender(), Bytes('balance')) - amount.get()",
                    0,
                ),
            },
        ),
        (
            213,
            {
                (3, 11): (
                    "App.localPut(Txn.sender(), Bytes('balance'), App.localGet(Txn.sender(), Bytes('balance')) - amount.get())",
                    0,
                ),
                (3, 10): (
                    "App.localPut(Txn.sender(), Bytes('balance'), App.localGet(Txn.sender(), Bytes('balance')) - amount.get())",
                    0,
                ),
            },
        ),
        (
            214,
            {
                (3, 11): ("InnerTxnBuilder.Begin()", 0),
                (3, 10): ("InnerTxnBuilder.Begin()", 0),
            },
        ),
        (
            215,
            {
                (3, 11): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
                (3, 10): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
            },
        ),
        (
            216,
            {
                (3, 11): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
                (3, 10): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
            },
        ),
        (
            217,
            {(3, 11): ("recipient.address()", 0), (3, 10): ("recipient.address()", 0)},
        ),
        (
            218,
            {(3, 11): ("recipient.address()", 0), (3, 10): ("recipient.address()", 0)},
        ),
        (
            219,
            {
                (3, 11): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
                (3, 10): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
            },
        ),
        (220, {(3, 11): ("amount.get()", 0), (3, 10): ("amount.get()", 0)}),
        (
            221,
            {
                (3, 11): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
                (3, 10): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
            },
        ),
        (222, {(3, 11): ("Int(0)", 0), (3, 10): ("Int(0)", 0)}),
        (
            223,
            {
                (3, 11): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
                (3, 10): (
                    "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                    0,
                ),
            },
        ),
        (
            224,
            {
                (3, 11): ("InnerTxnBuilder.Submit()", 0),
                (3, 10): ("InnerTxnBuilder.Submit()", 0),
            },
        ),
        (
            225,
            {
                (3, 11): (
                    "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), approval_filename=filename, with_sourcemaps=True)",
                    0,
                ),
                (3, 10): ("InnerTxnBuilder.Submit()", 0),
            },
        ),
    ]
    assert len(expected) == len(actual)

    version = sys.version_info[:2]
    flakes_for_310 = [d[(3, 10)] for _, d in expected]
    expected_for_311 = [d[(3, 11)] for _, d in expected]

    flake_count = 0
    for i, a in enumerate(actual):
        e = expected_for_311[i]
        if version >= (3, 11):
            assert (
                a == e
            ), f"""discrepancy at {i=} 
expected:
{e}
!= actual:
{a}"""
        else:
            if a != e:
                f = flakes_for_310[i]
                assert (
                    a == f
                ), f"""discrepancy at {i=} 
expected flake (current {flake_count=}):
{f}
!= actual:
{a}"""
                flake_count += 1

    print(f"TOTAL {flake_count=}")
