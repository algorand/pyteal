"""
This file monkey-patches ConfigParser in order to enable source mapping
and test the results of source mapping various PyTeal apps.
"""

from configparser import ConfigParser
from copy import deepcopy
from pathlib import Path
import pytest
import sys
from typing import Literal
from unittest import mock

# TODO: DO NOT MERGE WITHOUT HAVING DEALT WITH CASES 37 & 38 (and fixing test_constructs to use Router._build_impl)
BRUTE_FORCE_TERRIBLE_SKIPPING = """cannot properly handle @router.method source maps
and haven't yet agreed to abandon"""


ALGOBANK = Path.cwd() / "examples" / "application" / "abi"

FIXTURES = Path.cwd() / "tests" / "unit" / "sourcemaps"


@pytest.fixture
def mock_ConfigParser():
    patcher = mock.patch.object(ConfigParser, "getboolean", return_value=True)
    patcher.start()
    yield
    patcher.stop()


@pytest.fixture
def context_StackFrame_keep_all_debugging():
    from pyteal.stack_frame import NatalStackFrame

    NatalStackFrame._keep_all_debugging = True
    yield
    NatalStackFrame._keep_all_debugging = False


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Currently, this test only works in python 3.11 and above",
)
@pytest.mark.serial
def test_r3sourcemap(mock_ConfigParser):
    from examples.application.abi.algobank import router
    from pyteal.ast.router import _RouterCompileInput
    from pyteal import OptimizeOptions
    from pyteal.compiler.sourcemap import R3SourceMap

    filename = "dummy filename"
    rci = _RouterCompileInput(
        version=6,
        assemble_constants=False,
        optimize=OptimizeOptions(scratch_slots=True),
        approval_filename=filename,
        with_sourcemaps=True,
    )
    compile_bundle = router._build_impl(rci)

    ptsm = compile_bundle.approval_sourcemapper
    assert ptsm

    actual_unparsed = [x._hybrid_w_offset() for x in ptsm._cached_tmis]
    assert_algobank_unparsed_as_expected(actual_unparsed)

    r3sm = ptsm._cached_r3sourcemap
    assert r3sm

    assert filename == r3sm.file
    assert str(r3sm.source_root).startswith(str(Path.cwd()))
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
    assert (
        "AA2DqB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACkBrB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADlBqB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACKrB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADLqB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACnBrB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADmBqB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AC/CjB;AACc;AAAd;AAA4C;AAAc;AAA3B;AAA/B;AAFuB;ADgDN;AAAA;AAAA;ACrCkB;AAAA;ADqClB;AAAA;AAAA;AAAA;AAAA;ACvCiB;AAAA;AAdtC;AAAA;AAAA;AACkB;AAAgB;AAAhB;AAAP;AADX;AAkCA;AAAA;AAAA;ADmBqB;AAAA;ACNN;AAAA;AAA0B;AAAA;AAA1B;AAAP;AACO;AAAA;AAA4B;AAA5B;AAAP;AAEI;AAAA;AACA;AACa;AAAA;AAAkB;AAA/B;AAAmD;AAAA;AAAnD;AAHJ;AAfR;AAwBA;AAAA;AAAA;AASmC;AAAgB;AAA7B;AATtB;AAaA;AAAA;AAAA;ADlBqB;AAAA;ACsCT;AACA;AACa;AAAc;AAA3B;AAA+C;AAA/C;AAHJ;AAKA;AACA;AAAA;AAG2B;AAAA;AAH3B;AAIyB;AAJzB;AAKsB;AALtB;AAQA;AAjCR"
        == r3sm_json["mappings"]
    )

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


@pytest.mark.serial
def test_reconstruct(mock_ConfigParser):
    from examples.application.abi.algobank import router
    from pyteal.ast.router import _RouterCompileInput
    from pyteal import OptimizeOptions

    rci = _RouterCompileInput(
        version=6,
        assemble_constants=False,
        optimize=OptimizeOptions(scratch_slots=True),
        with_sourcemaps=True,
    )
    compile_bundle = router._build_impl(rci)

    assert compile_bundle.approval_sourcemapper
    assert compile_bundle.clear_sourcemapper

    def compare_and_assert(file, sourcemap):
        with open(ALGOBANK / file, "r") as f:
            expected_lines = f.read().splitlines()
            actual_lines = sourcemap.pure_teal().splitlines()
            assert len(expected_lines) == len(actual_lines)
            assert expected_lines == actual_lines

    compare_and_assert("algobank_approval.teal", compile_bundle.approval_sourcemapper)
    compare_and_assert("algobank_clear_state.teal", compile_bundle.clear_sourcemapper)


@pytest.mark.serial
def test_mocked_config_for_frames(mock_ConfigParser):
    config = ConfigParser()
    assert config.getboolean("pyteal-source-mapper", "enabled") is True
    from pyteal.stack_frame import NatalStackFrame

    assert NatalStackFrame.sourcemapping_is_off() is False
    assert NatalStackFrame.sourcemapping_is_off(_force_refresh=True) is False


def make(x, y, z):
    import pyteal as pt

    return pt.Int(x) + pt.Int(y) + pt.Int(z)


@pytest.mark.serial
def test_lots_o_indirection(mock_ConfigParser):
    import pyteal as pt

    e1 = pt.Seq(pt.Pop(make(1, 2, 3)), pt.Pop(make(4, 5, 6)), make(7, 8, 9))

    @pt.Subroutine(pt.TealType.uint64)
    def foo(x):
        return pt.Seq(pt.Pop(e1), e1)

    pt.Compilation(foo(pt.Int(42)), pt.Mode.Application, version=6)._compile_impl(
        with_sourcemap=True
    )


@pytest.mark.serial
def test_frame_info_is_right_before_core_last_drop_idx(
    context_StackFrame_keep_all_debugging,
):
    import pyteal as pt
    from pyteal.stack_frame import StackFrame

    e1 = pt.Seq(pt.Pop(make(1, 2, 3)), pt.Pop(make(4, 5, 6)), make(7, 8, 9))

    frame_infos = e1.stack_frames._frames
    last_drop_idx = 1
    assert StackFrame._frame_info_is_right_before_core(
        frame_infos[last_drop_idx].frame_info
    ), "Uh oh! Something about NatalStackFrame as changes which puts in jeopardy Source Map functionality"


# ### -----------------BEGIN: SANITY CHECKS SURVEY MOST PYTEAL CONSTRUCTS ----------------- ### #


P = "#pragma version {v}"  # fill the template at runtime

C = "comp._compile_impl(with_sourcemap=True)"
R = "expr._build_impl(rci)"

BIG_A = "pt.And(pt.Gtxn[0].rekey_to() == pt.Global.zero_address(), pt.Gtxn[1].rekey_to() == pt.Global.zero_address(), pt.Gtxn[2].rekey_to() == pt.Global.zero_address(), pt.Gtxn[3].rekey_to() == pt.Global.zero_address(), pt.Gtxn[4].rekey_to() == pt.Global.zero_address(), pt.Gtxn[0].last_valid() == pt.Gtxn[1].last_valid(), pt.Gtxn[1].last_valid() == pt.Gtxn[2].last_valid(), pt.Gtxn[2].last_valid() == pt.Gtxn[3].last_valid(), pt.Gtxn[3].last_valid() == pt.Gtxn[4].last_valid(), pt.Gtxn[0].type_enum() == pt.TxnType.AssetTransfer, pt.Gtxn[0].xfer_asset() == asset_c, pt.Gtxn[0].receiver() == receiver)"
BIG_OR = "pt.Or(pt.App.globalGet(pt.Bytes('paused')), pt.App.localGet(pt.Int(0), pt.Bytes('frozen')), pt.App.localGet(pt.Int(1), pt.Bytes('frozen')), pt.App.localGet(pt.Int(0), pt.Bytes('lock until')) >= pt.Global.latest_timestamp(), pt.App.localGet(pt.Int(1), pt.Bytes('lock until')) >= pt.Global.latest_timestamp(), pt.App.globalGet(pt.Concat(pt.Bytes('rule'), pt.Itob(pt.App.localGet(pt.Int(0), pt.Bytes('transfer group'))), pt.Itob(pt.App.localGet(pt.Int(1), pt.Bytes('transfer group'))))))"
BIG_C = "pt.Cond([pt.Txn.application_id() == pt.Int(0), foo], [pt.Txn.on_completion() == pt.OnComplete.DeleteApplication, pt.Return(is_admin)], [pt.Txn.on_completion() == pt.OnComplete.UpdateApplication, pt.Return(is_admin)], [pt.Txn.on_completion() == pt.OnComplete.CloseOut, foo], [pt.Txn.on_completion() == pt.OnComplete.OptIn, foo], [pt.Txn.application_args[0] == pt.Bytes('set admin'), foo], [pt.Txn.application_args[0] == pt.Bytes('mint'), foo], [pt.Txn.application_args[0] == pt.Bytes('transfer'), foo], [pt.Txn.accounts[4] == pt.Bytes('foo'), foo])"
BIG_W = "pt.While(i.load() < pt.Global.group_size())"
BIG_F = "pt.For(i.store(pt.Int(0)), i.load() < pt.Global.group_size(), i.store(i.load() + pt.Int(1)))"
BIG_A2 = "pt.And(pt.Int(1) - pt.Int(2), pt.Not(pt.Int(3)), pt.Int(4) ^ pt.Int(5), ~pt.Int(6), pt.BytesEq(pt.Bytes('7'), pt.Bytes('8')), pt.GetBit(pt.Int(9), pt.Int(10)), pt.SetBit(pt.Int(11), pt.Int(12), pt.Int(13)), pt.GetByte(pt.Bytes('14'), pt.Int(15)), pt.Btoi(pt.Concat(pt.BytesDiv(pt.Bytes('101'), pt.Bytes('102')), pt.BytesNot(pt.Bytes('103')), pt.BytesZero(pt.Int(10)), pt.SetBit(pt.Bytes('105'), pt.Int(106), pt.Int(107)), pt.SetByte(pt.Bytes('108'), pt.Int(109), pt.Int(110)))))"
BIG_C2 = "pt.Concat(pt.BytesDiv(pt.Bytes('101'), pt.Bytes('102')), pt.BytesNot(pt.Bytes('103')), pt.BytesZero(pt.Int(10)), pt.SetBit(pt.Bytes('105'), pt.Int(106), pt.Int(107)), pt.SetByte(pt.Bytes('108'), pt.Int(109), pt.Int(110)))"


def abi_named_tuple_example(pt):
    NUM_OPTIONS = 0

    class PollStatus(pt.abi.NamedTuple):
        question: pt.abi.Field[pt.abi.String]
        can_resubmit: pt.abi.Field[pt.abi.Bool]
        is_open: pt.abi.Field[pt.abi.Bool]
        results: pt.abi.Field[
            pt.abi.StaticArray[
                pt.abi.Tuple2[pt.abi.String, pt.abi.Uint64], Literal[NUM_OPTIONS]  # type: ignore
            ]
        ]

    @pt.ABIReturnSubroutine
    def status(*, output: PollStatus) -> pt.Expr:  # type: ignore
        """Get the status of this poll.

        Returns:
            A tuple containing the following information, in order: the question is poll is asking,
            whether the poll allows resubmission, whether the poll is open, and an array of the poll's
            current results. This array contains one entry per option, and each entry is a tuple of that
            option's value and the number of accounts who have voted for it.
        """
        question = pt.abi.make(pt.abi.String)
        can_resubmit = pt.abi.make(pt.abi.Bool)
        is_open = pt.abi.make(pt.abi.Bool)
        results = pt.abi.make(pt.abi.StaticArray[pt.abi.Tuple2[pt.abi.String, pt.abi.Uint64], Literal[NUM_OPTIONS]])  # type: ignore
        return pt.Seq(
            question.set(pt.App.globalGet(pt.Bytes("1"))),
            can_resubmit.set(pt.App.globalGet(pt.Bytes("2"))),
            is_open.set(pt.App.globalGet(pt.Bytes("3"))),
            results.set([]),
            output.set(question, can_resubmit, is_open, results),
        )

    output = PollStatus()
    return pt.Seq(status().store_into(output), pt.Int(1))  # type: ignore


def abi_method_return_example(pt):
    @pt.ABIReturnSubroutine
    def abi_sum(
        toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64  # type: ignore
    ) -> pt.Expr:  # type: ignore
        i = pt.ScratchVar(pt.TealType.uint64)
        valueAtIndex = pt.abi.Uint64()
        return pt.Seq(
            output.set(0),
            pt.For(
                i.store(pt.Int(0)),
                i.load() < toSum.length(),
                i.store(i.load() + pt.Int(1)),
            ).Do(
                pt.Seq(
                    toSum[i.load()].store_into(valueAtIndex),
                    output.set(output.get() + valueAtIndex.get()),
                )
            ),
        )

    return pt.Seq(
        (to_sum_arr := pt.abi.make(pt.abi.DynamicArray[pt.abi.Uint64])).decode(
            pt.Txn.application_args[1]
        ),
        (res := pt.abi.Uint64()).set(abi_sum(to_sum_arr)),  # type: ignore
        pt.abi.MethodReturn(res),
        pt.Approve(),
    )


def router_example_method(pt):
    on_completion_actions = pt.BareCallActions(
        opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes("optin call"))),
    )
    router = pt.Router("questionable", on_completion_actions, clear_state=pt.Approve())

    @router.method
    def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:  # type: ignore
        return output.set(a.get() + b.get())

    return router


def router_static_abisubroutine(pt):
    AppId = pt.abi.Uint64

    class Foo:
        """Some class docstring"""

        page_size = pt.Int(128 - 1)

        account = pt.abi.Address()
        app_id = pt.abi.Uint64()

        @staticmethod
        @pt.ABIReturnSubroutine
        def set_foo(
            _app_id: AppId,
        ) -> pt.Expr:  # type: ignore
            "Some docstring"
            return Foo.app_id.set(_app_id)

    router = pt.Router("foo")
    router.add_method_handler(
        Foo.set_foo,
        "set_foo",
        pt.MethodConfig(no_op=pt.CallConfig.CALL),
        "Foo the foo",
    )
    return router


SUCCESSFUL_SUBROUTINE_LINENO = 302

CONSTRUCTS_LATEST_VERSION = 8


def test_constructs_handles_latest_pyteal():
    import pyteal as pt

    assert CONSTRUCTS_LATEST_VERSION == pt.MAX_PROGRAM_VERSION


@pytest.mark.serial
def test_hybrid_w_offset(mock_ConfigParser):
    import pyteal as pt

    router = router_static_abisubroutine(pt)
    rci = pt.ast.router._RouterCompileInput(
        version=7,
        assemble_constants=True,
        with_sourcemaps=True,
    )

    sourcemap = router._build_impl(rci).approval_sourcemapper

    # expected:
    etarget = "def set_foo(_app_id: AppId) -> pt.Expr:"
    func_source = f'@staticmethod\n@pt.ABIReturnSubroutine\n{etarget}\n    """Some docstring"""\n    return Foo.app_id.set(_app_id)'

    # actual:
    lbf = sourcemap._best_frames[-1]
    hwo = lbf._hybrid_w_offset()
    nsource = lbf.node_source()
    code = lbf.code()
    naive_line = lbf.frame_info.lineno

    # consistent across versions:
    assert etarget == hwo[0]
    assert func_source == nsource

    # inconsistent between 3.10 and 3.11:
    if sys.version_info[:2] <= (3, 10):
        assert 0 == hwo[1]
        assert "def set_foo(" == code
        assert SUCCESSFUL_SUBROUTINE_LINENO == naive_line
    else:
        assert 1 == hwo[1]
        assert "@pt.ABIReturnSubroutine" == code
        assert SUCCESSFUL_SUBROUTINE_LINENO - 1 == naive_line


CONSTRUCTS = [
    (  # 0: Int
        lambda pt: pt.Return(pt.Int(42)),
        [[P, C], ["int 42", "pt.Int(42)"], ["return", "pt.Return(pt.Int(42))"]],
    ),
    (lambda pt: pt.Int(42), [[P, C], ["int 42", "pt.Int(42)"], ["return", C]]),
    (  # 2: Bytes
        lambda pt: pt.Seq(pt.Pop(pt.Bytes("hello world")), pt.Int(1)),
        [
            [P, C],
            ['byte "hello world"', "pt.Bytes('hello world')"],
            ["pop", "pt.Pop(pt.Bytes('hello world'))"],
            ["int 1", "pt.Int(1)"],
            ["return", C],
        ],
    ),
    (  # 3: *
        lambda pt: pt.Int(2) * pt.Int(3),
        [
            [P, C],
            ["int 2", "pt.Int(2)"],
            ["int 3", "pt.Int(3)"],
            ["*", "pt.Int(2) * pt.Int(3)"],
            ["return", C],
        ],
    ),
    (  # 4: ^
        lambda pt: pt.Int(2) ^ pt.Int(3),
        [
            [P, C],
            ["int 2", "pt.Int(2)"],
            ["int 3", "pt.Int(3)"],
            ["^", "pt.Int(2) ^ pt.Int(3)"],
            ["return", C],
        ],
    ),
    (  # 5: +*
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
    (  # 6: ~
        lambda pt: ~pt.Int(1),
        [[P, C], ["int 1", "pt.Int(1)"], ["~", "~pt.Int(1)"], ["return", C]],
    ),
    (  # 7: And Or
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
    (  # 8: Btoi BytesAnd
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
    (  # 9: Btoi BytesZero
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
    (  # 10: BytesNot
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
    (  # 11: Get/SetBit
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
    (  # 12: Get/SetByte
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
    (  # 13: Concat
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
    (  # 14: Substring
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
    (  # 15: Extract
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
    (  # 16: Txn
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
    (  # 17: Cond
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
    (  # 18: Tmpl Gtxn TxnType
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
            ),
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
    (  # 19: Txn.application_args
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
    (  # 20: App
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
    (  # 21: EcdsaCurve Sha512_256
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
    (  # 22: ScratchVar (simple Assert )
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
    (  # 23: DynamicScratchVar
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
    (  # 24: If/Then/Else ImportScratchVaplue
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
    (  # 25: If/Then/ElseIf/ElseIf/Else
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
    (  # 26: While/Do
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
    (  # 27: For/Do
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
    (  # 28: For/Do nested with If/Then/ElseIf/Then + Break/Continue
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
    (  # 29: For/Do w embedded Cond + Break/Continue
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
    (  # 30: While/Do w empbedded Cond + Break/Continue
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
    (  # 31: Assert (varargs)
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
    (  # 33 - ABI Subroutine + NamedTuple (scratch slots)
        abi_named_tuple_example,
        [
            [P, C],
            ("callsub status_0", "status()"),
            ("store 0", "status().store_into(output)"),
            ("int 1", "pt.Int(1)"),
            ("return", C),
            ("", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("// status", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("status_0:", "def status(*, output: PollStatus) -> pt.Expr:"),
            ('byte "1"', "pt.Bytes('1')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('1'))"),
            ("store 2", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("load 2", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("len", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("itob", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("extract 6 0", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("load 2", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("concat", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("store 2", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ('byte "2"', "pt.Bytes('2')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('2'))"),
            ("!", "can_resubmit.set(pt.App.globalGet(pt.Bytes('2')))"),
            ("!", "can_resubmit.set(pt.App.globalGet(pt.Bytes('2')))"),
            ("store 3", "can_resubmit.set(pt.App.globalGet(pt.Bytes('2')))"),
            ('byte "3"', "pt.Bytes('3')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('3'))"),
            ("!", "is_open.set(pt.App.globalGet(pt.Bytes('3')))"),
            ("!", "is_open.set(pt.App.globalGet(pt.Bytes('3')))"),
            ("store 4", "is_open.set(pt.App.globalGet(pt.Bytes('3')))"),
            ('byte ""', "results.set([])"),
            ("store 5", "results.set([])"),
            ("load 2", "output.set(question, can_resubmit, is_open, results)"),
            ("store 9", "output.set(question, can_resubmit, is_open, results)"),
            ("load 9", "output.set(question, can_resubmit, is_open, results)"),
            ("store 8", "output.set(question, can_resubmit, is_open, results)"),
            ("int 5", "output.set(question, can_resubmit, is_open, results)"),
            ("store 6", "output.set(question, can_resubmit, is_open, results)"),
            ("load 6", "output.set(question, can_resubmit, is_open, results)"),
            ("load 9", "output.set(question, can_resubmit, is_open, results)"),
            ("len", "output.set(question, can_resubmit, is_open, results)"),
            ("+", "output.set(question, can_resubmit, is_open, results)"),
            ("store 7", "output.set(question, can_resubmit, is_open, results)"),
            ("load 7", "output.set(question, can_resubmit, is_open, results)"),
            ("int 65536", "output.set(question, can_resubmit, is_open, results)"),
            ("<", "output.set(question, can_resubmit, is_open, results)"),
            ("assert", "output.set(question, can_resubmit, is_open, results)"),
            ("load 6", "output.set(question, can_resubmit, is_open, results)"),
            ("itob", "output.set(question, can_resubmit, is_open, results)"),
            ("extract 6 0", "output.set(question, can_resubmit, is_open, results)"),
            ("byte 0x00", "output.set(question, can_resubmit, is_open, results)"),
            ("int 0", "output.set(question, can_resubmit, is_open, results)"),
            ("load 3", "output.set(question, can_resubmit, is_open, results)"),
            ("setbit", "output.set(question, can_resubmit, is_open, results)"),
            ("int 1", "output.set(question, can_resubmit, is_open, results)"),
            ("load 4", "output.set(question, can_resubmit, is_open, results)"),
            ("setbit", "output.set(question, can_resubmit, is_open, results)"),
            ("concat", "output.set(question, can_resubmit, is_open, results)"),
            ("load 5", "output.set(question, can_resubmit, is_open, results)"),
            ("store 9", "output.set(question, can_resubmit, is_open, results)"),
            ("load 8", "output.set(question, can_resubmit, is_open, results)"),
            ("load 9", "output.set(question, can_resubmit, is_open, results)"),
            ("concat", "output.set(question, can_resubmit, is_open, results)"),
            ("store 8", "output.set(question, can_resubmit, is_open, results)"),
            ("load 7", "output.set(question, can_resubmit, is_open, results)"),
            ("store 6", "output.set(question, can_resubmit, is_open, results)"),
            ("load 6", "output.set(question, can_resubmit, is_open, results)"),
            ("itob", "output.set(question, can_resubmit, is_open, results)"),
            ("extract 6 0", "output.set(question, can_resubmit, is_open, results)"),
            ("concat", "output.set(question, can_resubmit, is_open, results)"),
            ("load 8", "output.set(question, can_resubmit, is_open, results)"),
            ("concat", "output.set(question, can_resubmit, is_open, results)"),
            ("store 1", "output.set(question, can_resubmit, is_open, results)"),
            ("load 1", "status().store_into(output)"),
            ("retsub", "def status(*, output: PollStatus) -> pt.Expr:"),
        ],
        5,
        "Application",
        dict(frame_pointers=False),
    ),
    (  # 34 - ABI Subroutine + NamedTuple (frame pointers)
        abi_named_tuple_example,
        [
            [P, C],
            ("callsub status_0", "status()"),
            ("store 0", "status().store_into(output)"),
            ("int 1", "pt.Int(1)"),
            ("return", C),
            ("", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("// status", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("status_0:", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("proto 0 1", "def status(*, output: PollStatus) -> pt.Expr:"),
            ('byte ""', "def status(*, output: PollStatus) -> pt.Expr:"),
            ("dup", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("int 0", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("dup", "def status(*, output: PollStatus) -> pt.Expr:"),
            ('byte ""', "def status(*, output: PollStatus) -> pt.Expr:"),
            ("int 0", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("dup", "def status(*, output: PollStatus) -> pt.Expr:"),
            ('byte ""', "def status(*, output: PollStatus) -> pt.Expr:"),
            ("dup", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("int 0", "def status(*, output: PollStatus) -> pt.Expr:"),
            ("dup", "def status(*, output: PollStatus) -> pt.Expr:"),
            ('byte ""', "def status(*, output: PollStatus) -> pt.Expr:"),
            ("dup", "def status(*, output: PollStatus) -> pt.Expr:"),
            ('byte "1"', "pt.Bytes('1')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('1'))"),
            ("frame_bury 1", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("frame_dig 1", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("len", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("itob", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("extract 6 0", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("frame_dig 1", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("concat", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ("frame_bury 1", "question.set(pt.App.globalGet(pt.Bytes('1')))"),
            ('byte "2"', "pt.Bytes('2')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('2'))"),
            ("!", "can_resubmit.set(pt.App.globalGet(pt.Bytes('2')))"),
            ("!", "can_resubmit.set(pt.App.globalGet(pt.Bytes('2')))"),
            ("frame_bury 2", "can_resubmit.set(pt.App.globalGet(pt.Bytes('2')))"),
            ('byte "3"', "pt.Bytes('3')"),
            ("app_global_get", "pt.App.globalGet(pt.Bytes('3'))"),
            ("!", "is_open.set(pt.App.globalGet(pt.Bytes('3')))"),
            ("!", "is_open.set(pt.App.globalGet(pt.Bytes('3')))"),
            ("frame_bury 3", "is_open.set(pt.App.globalGet(pt.Bytes('3')))"),
            ('byte ""', "results.set([])"),
            ("frame_bury 4", "results.set([])"),
            ("frame_dig 1", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_bury 12", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 12", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_bury 11", "output.set(question, can_resubmit, is_open, results)"),
            ("int 5", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_bury 9", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 9", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 12", "output.set(question, can_resubmit, is_open, results)"),
            ("len", "output.set(question, can_resubmit, is_open, results)"),
            ("+", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_bury 10", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 10", "output.set(question, can_resubmit, is_open, results)"),
            ("int 65536", "output.set(question, can_resubmit, is_open, results)"),
            ("<", "output.set(question, can_resubmit, is_open, results)"),
            ("assert", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 9", "output.set(question, can_resubmit, is_open, results)"),
            ("itob", "output.set(question, can_resubmit, is_open, results)"),
            ("extract 6 0", "output.set(question, can_resubmit, is_open, results)"),
            ("byte 0x00", "output.set(question, can_resubmit, is_open, results)"),
            ("int 0", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 2", "output.set(question, can_resubmit, is_open, results)"),
            ("setbit", "output.set(question, can_resubmit, is_open, results)"),
            ("int 1", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 3", "output.set(question, can_resubmit, is_open, results)"),
            ("setbit", "output.set(question, can_resubmit, is_open, results)"),
            ("concat", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 4", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_bury 12", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 11", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 12", "output.set(question, can_resubmit, is_open, results)"),
            ("concat", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_bury 11", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 10", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_bury 9", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 9", "output.set(question, can_resubmit, is_open, results)"),
            ("itob", "output.set(question, can_resubmit, is_open, results)"),
            ("extract 6 0", "output.set(question, can_resubmit, is_open, results)"),
            ("concat", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_dig 11", "output.set(question, can_resubmit, is_open, results)"),
            ("concat", "output.set(question, can_resubmit, is_open, results)"),
            ("frame_bury 0", "output.set(question, can_resubmit, is_open, results)"),
            ("retsub", "def status(*, output: PollStatus) -> pt.Expr:"),
        ],
        8,
        "Application",
        dict(frame_pointers=True),
    ),
    (  # 35 - ABI Subroutine + MethodReturn (scratch slots)
        abi_method_return_example,
        [
            [P, C],
            ("txna ApplicationArgs 1", "pt.Txn.application_args[1]"),
            (
                "store 0",
                "(to_sum_arr := pt.abi.make(pt.abi.DynamicArray[pt.abi.Uint64])).decode(pt.Txn.application_args[1])",
            ),
            ("load 0", C),
            ("callsub abisum_0", "abi_sum(to_sum_arr)"),
            ("store 1", "(res := pt.abi.Uint64()).set(abi_sum(to_sum_arr))"),
            ("byte 0x151f7c75", C),
            ("load 1", C),
            ("itob", C),
            ("concat", C),
            ("log", C),
            ("int 1", "pt.Approve()"),
            ("return", "pt.Approve()"),
            (
                "",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "// abi_sum",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "abisum_0:",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            ("store 2", "(res := pt.abi.Uint64()).set(abi_sum(to_sum_arr))"),
            ("int 0", "output.set(0)"),
            ("store 3", "output.set(0)"),
            ("int 0", "pt.Int(0)"),
            ("store 4", "i.store(pt.Int(0))"),
            (
                "abisum_0_l1:",
                "pt.For(i.store(pt.Int(0)), i.load() < toSum.length(), i.store(i.load() + pt.Int(1)))",
            ),
            ("load 4", "i.load()"),
            ("load 2", "toSum.length()"),
            ("int 0", "toSum.length()"),
            ("extract_uint16", "toSum.length()"),
            ("store 6", "toSum.length()"),
            ("load 6", "toSum.length()"),
            ("<", "i.load() < toSum.length()"),
            (
                "bz abisum_0_l3",
                "pt.For(i.store(pt.Int(0)), i.load() < toSum.length(), i.store(i.load() + pt.Int(1)))",
            ),
            ("load 2", "toSum[i.load()].store_into(valueAtIndex)"),
            ("int 8", "toSum[i.load()].store_into(valueAtIndex)"),
            ("load 4", "i.load()"),
            ("*", "toSum[i.load()].store_into(valueAtIndex)"),
            ("int 2", "toSum[i.load()].store_into(valueAtIndex)"),
            ("+", "toSum[i.load()].store_into(valueAtIndex)"),
            ("extract_uint64", "toSum[i.load()].store_into(valueAtIndex)"),
            ("store 5", "toSum[i.load()].store_into(valueAtIndex)"),
            ("load 3", "output.get()"),
            ("load 5", "valueAtIndex.get()"),
            ("+", "output.get() + valueAtIndex.get()"),
            ("store 3", "output.set(output.get() + valueAtIndex.get())"),
            ("load 4", "i.load()"),
            ("int 1", "pt.Int(1)"),
            ("+", "i.load() + pt.Int(1)"),
            ("store 4", "i.store(i.load() + pt.Int(1))"),
            (
                "b abisum_0_l1",
                "pt.For(i.store(pt.Int(0)), i.load() < toSum.length(), i.store(i.load() + pt.Int(1)))",
            ),
            (
                "abisum_0_l3:",
                "pt.For(i.store(pt.Int(0)), i.load() < toSum.length(), i.store(i.load() + pt.Int(1)))",
            ),
            ("load 3", "(res := pt.abi.Uint64()).set(abi_sum(to_sum_arr))"),
            (
                "retsub",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
        ],
        5,
        "Application",
        dict(frame_pointers=False),
    ),
    (  # 36 - ABI Subroutine + MethodReturn (frame pointers)
        abi_method_return_example,
        [
            [P, C],
            ("txna ApplicationArgs 1", "pt.Txn.application_args[1]"),
            (
                "store 0",
                "(to_sum_arr := pt.abi.make(pt.abi.DynamicArray[pt.abi.Uint64])).decode(pt.Txn.application_args[1])",
            ),
            ("load 0", C),
            ("callsub abisum_0", "abi_sum(to_sum_arr)"),
            ("store 1", "(res := pt.abi.Uint64()).set(abi_sum(to_sum_arr))"),
            ("byte 0x151f7c75", C),
            ("load 1", C),
            ("itob", C),
            ("concat", C),
            ("log", C),
            ("int 1", "pt.Approve()"),
            ("return", "pt.Approve()"),
            (
                "",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "// abi_sum",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "abisum_0:",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "proto 1 1",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "int 0",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "dupn 3",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            ("int 0", "output.set(0)"),
            ("frame_bury 0", "output.set(0)"),
            ("int 0", "pt.Int(0)"),
            ("store 2", "i.store(pt.Int(0))"),
            (
                "abisum_0_l1:",
                "pt.For(i.store(pt.Int(0)), i.load() < toSum.length(), i.store(i.load() + pt.Int(1)))",
            ),
            ("load 2", "i.load()"),
            ("frame_dig -1", "toSum.length()"),
            ("int 0", "toSum.length()"),
            ("extract_uint16", "toSum.length()"),
            ("frame_bury 2", "toSum.length()"),
            ("frame_dig 2", "toSum.length()"),
            ("<", "i.load() < toSum.length()"),
            (
                "bz abisum_0_l3",
                "pt.For(i.store(pt.Int(0)), i.load() < toSum.length(), i.store(i.load() + pt.Int(1)))",
            ),
            ("frame_dig -1", "toSum[i.load()].store_into(valueAtIndex)"),
            ("int 8", "toSum[i.load()].store_into(valueAtIndex)"),
            ("load 2", "i.load()"),
            ("*", "toSum[i.load()].store_into(valueAtIndex)"),
            ("int 2", "toSum[i.load()].store_into(valueAtIndex)"),
            ("+", "toSum[i.load()].store_into(valueAtIndex)"),
            ("extract_uint64", "toSum[i.load()].store_into(valueAtIndex)"),
            ("frame_bury 1", "toSum[i.load()].store_into(valueAtIndex)"),
            ("frame_dig 0", "output.get()"),
            ("frame_dig 1", "valueAtIndex.get()"),
            ("+", "output.get() + valueAtIndex.get()"),
            ("frame_bury 0", "output.set(output.get() + valueAtIndex.get())"),
            ("load 2", "i.load()"),
            ("int 1", "pt.Int(1)"),
            ("+", "i.load() + pt.Int(1)"),
            ("store 2", "i.store(i.load() + pt.Int(1))"),
            (
                "b abisum_0_l1",
                "pt.For(i.store(pt.Int(0)), i.load() < toSum.length(), i.store(i.load() + pt.Int(1)))",
            ),
            (
                "abisum_0_l3:",
                "pt.For(i.store(pt.Int(0)), i.load() < toSum.length(), i.store(i.load() + pt.Int(1)))",
            ),
            (
                "retsub",
                "def abi_sum(toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
        ],
        8,
        "Application",
        dict(frame_pointers=True),
    ),
    (  # 37 - Router (scratch slots)
        router_example_method,
        [
            [P, R],
            (
                "txn NumAppArgs",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "int 0",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "==",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "bnz main_l4",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "txna ApplicationArgs 0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                'method "add(uint64,uint64)uint64"',
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "==",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "bnz main_l3",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "err",
                "expr.compile(version=version, assemble_constants=False, optimize=optimize, with_sourcemaps=True)",
            ),
            (
                "main_l3:",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "txn OnCompletion",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "int NoOp",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "==",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "txn ApplicationID",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "int 0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "!=",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "&&",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "assert",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "txna ApplicationArgs 1",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "btoi",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "store 0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "txna ApplicationArgs 2",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "btoi",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "store 1",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "load 0",
                "expr.compile(version=version, assemble_constants=False, optimize=optimize, with_sourcemaps=True)",
            ),
            (
                "load 1",
                "expr.compile(version=version, assemble_constants=False, optimize=optimize, with_sourcemaps=True)",
            ),
            (
                "callsub add_0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "store 2",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "byte 0x151f7c75",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "load 2",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "itob",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "concat",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "log",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "int 1",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "return",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "main_l4:",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "txn OnCompletion",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "int OptIn",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "==",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "bnz main_l6",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "err",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "main_l6:",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "txn ApplicationID",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "int 0",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "!=",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "assert",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            ('byte "optin call"', "pt.Bytes('optin call')"),
            ("log", "pt.Log(pt.Bytes('optin call'))"),
            (
                "int 1",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "return",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "// add",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "add_0:",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "store 4",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "store 3",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            ("load 3", "a.get()"),
            ("load 4", "b.get()"),
            ("+", "a.get() + b.get()"),
            ("store 5", "output.set(a.get() + b.get())"),
            (
                "load 5",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "retsub",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
        ],
        5,
        "Application",
        dict(frame_pointers=False),
    ),
    (  # 38 - Router (frame pointers)
        router_example_method,
        [
            [P, R],
            (
                "txn NumAppArgs",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "int 0",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "==",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "bnz main_l4",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "txna ApplicationArgs 0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                'method "add(uint64,uint64)uint64"',
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "==",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "bnz main_l3",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "err",
                "expr.compile(version=version, assemble_constants=False, optimize=optimize, with_sourcemaps=True)",
            ),
            (
                "main_l3:",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "txn OnCompletion",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "int NoOp",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "==",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "txn ApplicationID",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "int 0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "!=",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "&&",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "assert",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "txna ApplicationArgs 1",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "btoi",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "store 0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "txna ApplicationArgs 2",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "btoi",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "store 1",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "load 0",
                "expr.compile(version=version, assemble_constants=False, optimize=optimize, with_sourcemaps=True)",
            ),
            (
                "load 1",
                "expr.compile(version=version, assemble_constants=False, optimize=optimize, with_sourcemaps=True)",
            ),
            (
                "callsub add_0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "store 2",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "byte 0x151f7c75",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "load 2",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "itob",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "concat",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "log",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "int 1",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "return",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "main_l4:",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "txn OnCompletion",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "int OptIn",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "==",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "bnz main_l6",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "err",
                "pt.BareCallActions(opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes('optin call'))))",
            ),
            (
                "main_l6:",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "txn ApplicationID",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "int 0",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "!=",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "assert",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            ('byte "optin call"', "pt.Bytes('optin call')"),
            ("log", "pt.Log(pt.Bytes('optin call'))"),
            (
                "int 1",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "return",
                "pt.Router('questionable', on_completion_actions, clear_state=pt.Approve())",
            ),
            (
                "",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "// add",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "add_0:",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "proto 2 1",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            (
                "int 0",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
            ("frame_dig -2", "a.get()"),
            ("frame_dig -1", "b.get()"),
            ("+", "a.get() + b.get()"),
            ("frame_bury 0", "output.set(a.get() + b.get())"),
            (
                "retsub",
                "def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:",
            ),
        ],
        8,
        "Application",
        dict(frame_pointers=True),
    ),
    (  # 39 - Router static subroutine (scratch slots)
        router_static_abisubroutine,
        [
            [P, R],
            ("txna ApplicationArgs 0", R),
            ('method "set_foo(uint64)void"', R),
            ("==", R),
            ("bnz main_l2", R),
            ("err", R),
            ("main_l2:", R),
            (
                "txn OnCompletion",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "int NoOp",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "==",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "txn ApplicationID",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "int 0",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "!=",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "&&",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            ("assert", R),
            ("txna ApplicationArgs 1", R),
            ("btoi", R),
            ("store 1", R),
            ("load 1", R),
            ("callsub setfoo_0", R),
            ("int 1", R),
            ("return", R),
            ("", "def set_foo(_app_id: AppId) -> pt.Expr:"),
            ("// set_foo", "def set_foo(_app_id: AppId) -> pt.Expr:"),
            ("setfoo_0:", "def set_foo(_app_id: AppId) -> pt.Expr:"),
            ("store 2", R),
            ("load 2", "Foo.app_id.set(_app_id)"),
            ("store 0", "Foo.app_id.set(_app_id)"),
            ("retsub", "def set_foo(_app_id: AppId) -> pt.Expr:"),
        ],
        5,
        "Application",
        dict(frame_pointers=False),
    ),
    (  # 40 - Router static subroutine (frame pointers)
        router_static_abisubroutine,
        [
            [P, R],
            ("txna ApplicationArgs 0", R),
            ('method "set_foo(uint64)void"', R),
            ("==", R),
            ("bnz main_l2", R),
            ("err", R),
            ("main_l2:", R),
            (
                "txn OnCompletion",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "int NoOp",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "==",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "txn ApplicationID",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "int 0",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "!=",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            (
                "&&",
                "router.add_method_handler(Foo.set_foo, 'set_foo', pt.MethodConfig(no_op=pt.CallConfig.CALL), 'Foo the foo')",
            ),
            ("assert", R),
            ("callsub setfoocaster_1", R),
            ("int 1", R),
            ("return", R),
            ("", "def set_foo(_app_id: AppId) -> pt.Expr:"),
            ("// set_foo", "def set_foo(_app_id: AppId) -> pt.Expr:"),
            ("setfoo_0:", "def set_foo(_app_id: AppId) -> pt.Expr:"),
            ("proto 1 0", "def set_foo(_app_id: AppId) -> pt.Expr:"),
            ("frame_dig -1", "Foo.app_id.set(_app_id)"),
            ("store 0", "Foo.app_id.set(_app_id)"),
            ("retsub", "def set_foo(_app_id: AppId) -> pt.Expr:"),
            ("", R),
            ("// set_foo_caster", R),
            ("setfoocaster_1:", R),
            ("proto 0 0", R),
            ("int 0", R),
            ("txna ApplicationArgs 1", R),
            ("btoi", R),
            ("frame_bury 0", R),
            ("frame_dig 0", R),
            ("callsub setfoo_0", R),
            ("retsub", R),
        ],
        8,
        "Application",
        dict(frame_pointers=True),
    ),
]

if BRUTE_FORCE_TERRIBLE_SKIPPING:
    del CONSTRUCTS[38]
    del CONSTRUCTS[37]


@pytest.mark.parametrize("i, test_case", enumerate(CONSTRUCTS))
@pytest.mark.parametrize("mode", ["Application", "Signature"])
@pytest.mark.parametrize("version", range(2, CONSTRUCTS_LATEST_VERSION + 1))
@pytest.mark.serial
def test_constructs(mock_ConfigParser, i, test_case, mode, version):
    import pyteal as pt

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
    optimize = None
    if len(test_case) > 4:
        optimize = pt.OptimizeOptions(**test_case[4])

    mode = getattr(pt.Mode, mode)
    if isinstance(expr, pt.Router):
        assert len(test_case) > 3 and fixed_mode == "Application"  # type: ignore

        rci = pt.ast.router._RouterCompileInput(
            version=version,
            assemble_constants=False,
            optimize=optimize,
            with_sourcemaps=True,
        )
        sourcemap = expr._build_impl(rci).approval_sourcemapper
    else:
        comp = pt.Compilation(
            expr, mode, version=version, assemble_constants=False, optimize=optimize
        )
        bundle = comp._compile_impl(with_sourcemap=True)
        sourcemap = bundle.sourcemapper

    msg = f"[CASE #{i}]: {expr=}"

    assert sourcemap, msg

    tmis = sourcemap.as_list()
    N = len(tmis)

    teal_linenos = [tmi.teal_lineno for tmi in tmis]
    assert list(range(1, N + 1)) == teal_linenos

    teal_lines = [tmi.teal_line for tmi in tmis]
    assert teal_lines == [
        l for chunk in sourcemap.teal_chunks for l in chunk.splitlines()
    ]

    unparsed = [tmi.hybrid_unparsed() for tmi in tmis]  # type: ignore
    msg = f"{msg}, {tmis=}"
    FORCE_FAIL_FOR_CASE_CREATION = False
    if FORCE_FAIL_FOR_CASE_CREATION:
        ouch = [(t, unparsed[i]) for i, t in enumerate(teal_lines)]
        print(ouch)
        x = "DEBUG" * 100
        assert not x, ouch

    expected_lines, expected_unparsed = list(zip(*line2unparsed))

    assert list(expected_lines) == teal_lines, msg
    assert list(expected_unparsed) == unparsed, msg


# ### -----------------END: SANITY CHECKS----------------- ### #


def assert_algobank_unparsed_as_expected(actual):
    expected = [
        (0, ("router._build_impl(rci)", 0)),
        (1, ("router._build_impl(rci)", 0)),
        (2, ("router._build_impl(rci)", 0)),
        (3, ("router._build_impl(rci)", 0)),
        (4, ("router._build_impl(rci)", 0)),
        (5, ("router._build_impl(rci)", 0)),
        (6, ("router._build_impl(rci)", 0)),
        (7, ("router._build_impl(rci)", 0)),
        (8, ("router._build_impl(rci)", 0)),
        (9, ("router._build_impl(rci)", 0)),
        (10, ("router._build_impl(rci)", 0)),
        (11, ("router._build_impl(rci)", 0)),
        (12, ("router._build_impl(rci)", 0)),
        (13, ("router._build_impl(rci)", 0)),
        (14, ("router._build_impl(rci)", 0)),
        (15, ("router._build_impl(rci)", 0)),
        (16, ("router._build_impl(rci)", 0)),
        (17, ("router._build_impl(rci)", 0)),
        (18, ("router._build_impl(rci)", 0)),
        (19, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (20, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (21, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (22, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (23, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (24, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (25, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (26, ("router._build_impl(rci)", 0)),
        (27, ("router._build_impl(rci)", 0)),
        (28, ("router._build_impl(rci)", 0)),
        (29, ("router._build_impl(rci)", 0)),
        (30, ("router._build_impl(rci)", 0)),
        (31, ("router._build_impl(rci)", 0)),
        (32, ("router._build_impl(rci)", 0)),
        (33, ("router._build_impl(rci)", 0)),
        (34, ("router._build_impl(rci)", 0)),
        (35, ("router._build_impl(rci)", 0)),
        (36, ("router._build_impl(rci)", 0)),
        (37, ("router._build_impl(rci)", 0)),
        (38, ("router._build_impl(rci)", 0)),
        (39, ("router._build_impl(rci)", 0)),
        (40, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (41, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (42, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (43, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (44, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (45, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (46, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (47, ("router._build_impl(rci)", 0)),
        (48, ("router._build_impl(rci)", 0)),
        (49, ("router._build_impl(rci)", 0)),
        (50, ("router._build_impl(rci)", 0)),
        (51, ("router._build_impl(rci)", 0)),
        (52, ("router._build_impl(rci)", 0)),
        (53, ("router._build_impl(rci)", 0)),
        (54, ("router._build_impl(rci)", 0)),
        (55, ("router._build_impl(rci)", 0)),
        (56, ("router._build_impl(rci)", 0)),
        (57, ("router._build_impl(rci)", 0)),
        (58, ("router._build_impl(rci)", 0)),
        (59, ("router._build_impl(rci)", 0)),
        (60, ("router._build_impl(rci)", 0)),
        (
            61,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            62,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            63,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            64,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            65,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            66,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            67,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            68,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            69,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            70,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            71,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            72,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            73,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            74,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            75,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (76, ("router._build_impl(rci)", 0)),
        (77, ("router._build_impl(rci)", 0)),
        (78, ("router._build_impl(rci)", 0)),
        (79, ("router._build_impl(rci)", 0)),
        (80, ("router._build_impl(rci)", 0)),
        (81, ("router._build_impl(rci)", 0)),
        (82, ("router._build_impl(rci)", 0)),
        (83, ("router._build_impl(rci)", 0)),
        (84, ("router._build_impl(rci)", 0)),
        (85, ("router._build_impl(rci)", 0)),
        (86, ("router._build_impl(rci)", 0)),
        (87, ("router._build_impl(rci)", 0)),
        (88, ("router._build_impl(rci)", 0)),
        (89, ("router._build_impl(rci)", 0)),
        (90, ("router._build_impl(rci)", 0)),
        (91, ("router._build_impl(rci)", 0)),
        (92, ("router._build_impl(rci)", 0)),
        (93, ("router._build_impl(rci)", 0)),
        (94, ("router._build_impl(rci)", 0)),
        (95, ("router._build_impl(rci)", 0)),
        (96, ("router._build_impl(rci)", 0)),
        (97, ("router._build_impl(rci)", 0)),
        (98, ("router._build_impl(rci)", 0)),
        (99, ("router._build_impl(rci)", 0)),
        (100, ("router._build_impl(rci)", 0)),
        (101, ("router._build_impl(rci)", 0)),
        (102, ("router._build_impl(rci)", 0)),
        (103, ("router._build_impl(rci)", 0)),
        (104, ("router._build_impl(rci)", 0)),
        (105, ("router._build_impl(rci)", 0)),
        (106, ("router._build_impl(rci)", 0)),
        (107, ("router._build_impl(rci)", 0)),
        (108, ("router._build_impl(rci)", 0)),
        (109, ("router._build_impl(rci)", 0)),
        (110, ("router._build_impl(rci)", 0)),
        (111, ("router._build_impl(rci)", 0)),
        (112, ("router._build_impl(rci)", 0)),
        (113, ("router._build_impl(rci)", 0)),
        (114, ("router._build_impl(rci)", 0)),
        (115, ("router._build_impl(rci)", 0)),
        (116, ("router._build_impl(rci)", 0)),
        (117, ("router._build_impl(rci)", 0)),
        (118, ("router._build_impl(rci)", 0)),
        (119, ("router._build_impl(rci)", 0)),
        (120, ("router._build_impl(rci)", 0)),
        (121, ("router._build_impl(rci)", 0)),
        (122, ("router._build_impl(rci)", 0)),
        (123, ("router._build_impl(rci)", 0)),
        (124, ("router._build_impl(rci)", 0)),
        (125, ("router._build_impl(rci)", 0)),
        (126, ("router._build_impl(rci)", 0)),
        (127, ("router._build_impl(rci)", 0)),
        (128, ("router._build_impl(rci)", 0)),
        (129, ("router._build_impl(rci)", 0)),
        (130, ("router._build_impl(rci)", 0)),
        (131, ("router._build_impl(rci)", 0)),
        (132, ("router._build_impl(rci)", 0)),
        (133, ("router._build_impl(rci)", 0)),
        (134, ("router._build_impl(rci)", 0)),
        (135, ("router._build_impl(rci)", 0)),
        (136, ("router._build_impl(rci)", 0)),
        (137, ("router._build_impl(rci)", 0)),
        (138, ("Bytes('lost')", 0)),
        (139, ("Bytes('lost')", 0)),
        (140, ("App.globalGet(Bytes('lost'))", 0)),
        (141, ("Txn.sender()", 0)),
        (142, ("Bytes('balance')", 0)),
        (143, ("App.localGet(Txn.sender(), Bytes('balance'))", 0)),
        (
            144,
            (
                "App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance'))",
                0,
            ),
        ),
        (
            145,
            (
                "App.globalPut(Bytes('lost'), App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance')))",
                0,
            ),
        ),
        (146, ("router._build_impl(rci)", 0)),
        (147, ("router._build_impl(rci)", 0)),
        (148, ("router._build_impl(rci)", 0)),
        (149, ("Approve()", 0)),
        (150, ("Approve()", 0)),
        (151, ("router._build_impl(rci)", 0)),
        (152, ("router._build_impl(rci)", 0)),
        (153, ("router._build_impl(rci)", 0)),
        (154, ("router._build_impl(rci)", 0)),
        (155, ("router._build_impl(rci)", 0)),
        (156, ("Approve()", 0)),
        (157, ("Approve()", 0)),
        (158, ("def assert_sender_is_creator() -> Expr:", 1)),
        (159, ("def assert_sender_is_creator() -> Expr:", 1)),
        (160, ("def assert_sender_is_creator() -> Expr:", 1)),
        (161, ("Txn.sender()", 0)),
        (162, ("Global.creator_address()", 0)),
        (163, ("Txn.sender() == Global.creator_address()", 0)),
        (164, ("Assert(Txn.sender() == Global.creator_address())", 0)),
        (165, ("def assert_sender_is_creator() -> Expr:", 1)),
        (
            166,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            167,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            168,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (169, ("router._build_impl(rci)", 0)),
        (170, ("router._build_impl(rci)", 0)),
        (171, ("payment.get()", 0)),
        (172, ("payment.get().sender()", 0)),
        (173, ("sender.address()", 0)),
        (174, ("sender.address()", 0)),
        (175, ("payment.get().sender() == sender.address()", 0)),
        (176, ("Assert(payment.get().sender() == sender.address())", 0)),
        (177, ("payment.get()", 0)),
        (178, ("payment.get().receiver()", 0)),
        (179, ("Global.current_application_address()", 0)),
        (180, ("payment.get().receiver() == Global.current_application_address()", 0)),
        (
            181,
            (
                "Assert(payment.get().receiver() == Global.current_application_address())",
                0,
            ),
        ),
        (182, ("sender.address()", 0)),
        (183, ("sender.address()", 0)),
        (184, ("Bytes('balance')", 0)),
        (185, ("sender.address()", 0)),
        (186, ("sender.address()", 0)),
        (187, ("Bytes('balance')", 0)),
        (188, ("App.localGet(sender.address(), Bytes('balance'))", 0)),
        (189, ("payment.get()", 0)),
        (190, ("payment.get().amount()", 0)),
        (
            191,
            (
                "App.localGet(sender.address(), Bytes('balance')) + payment.get().amount()",
                0,
            ),
        ),
        (
            192,
            (
                "App.localPut(sender.address(), Bytes('balance'), App.localGet(sender.address(), Bytes('balance')) + payment.get().amount())",
                0,
            ),
        ),
        (
            193,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (194, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (195, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (196, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (197, ("user.address()", 0)),
        (198, ("Bytes('balance')", 0)),
        (199, ("App.localGet(user.address(), Bytes('balance'))", 0)),
        (200, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (201, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (202, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (203, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (204, ("router._build_impl(rci)", 0)),
        (205, ("router._build_impl(rci)", 0)),
        (206, ("Txn.sender()", 0)),
        (207, ("Bytes('balance')", 0)),
        (208, ("Txn.sender()", 0)),
        (209, ("Bytes('balance')", 0)),
        (210, ("App.localGet(Txn.sender(), Bytes('balance'))", 0)),
        (211, ("amount.get()", 0)),
        (212, ("App.localGet(Txn.sender(), Bytes('balance')) - amount.get()", 0)),
        (
            213,
            (
                "App.localPut(Txn.sender(), Bytes('balance'), App.localGet(Txn.sender(), Bytes('balance')) - amount.get())",
                0,
            ),
        ),
        (214, ("InnerTxnBuilder.Begin()", 0)),
        (
            215,
            (
                "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                0,
            ),
        ),
        (
            216,
            (
                "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                0,
            ),
        ),
        (217, ("recipient.address()", 0)),
        (218, ("recipient.address()", 0)),
        (
            219,
            (
                "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                0,
            ),
        ),
        (220, ("amount.get()", 0)),
        (
            221,
            (
                "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                0,
            ),
        ),
        (222, ("Int(0)", 0)),
        (
            223,
            (
                "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})",
                0,
            ),
        ),
        (224, ("InnerTxnBuilder.Submit()", 0)),
        (225, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
    ]
    assert len(expected) == len(actual)
    print(list(enumerate(actual)))

    for i, a in enumerate(actual):
        assert (
            e := expected[i][1]
        ) == a, f"""discrepancy at index {i=} 
expected:
{e}
!= actual:
{a}"""
