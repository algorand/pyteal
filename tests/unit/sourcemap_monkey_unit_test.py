from ast import FunctionDef
from contextlib import contextmanager
from pathlib import Path
import pytest
import sys
from unittest import mock

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"

FIXTURES = Path.cwd() / "tests" / "unit" / "sourcemaps"


@pytest.fixture
def sourcemap_enabled():
    from feature_gates import FeatureGates

    previous = FeatureGates.sourcemap_enabled()
    FeatureGates.set_sourcemap_enabled(True)
    yield
    FeatureGates.set_sourcemap_enabled(previous)


@pytest.fixture
def StackFrame_keep_all_debugging():
    from pyteal.stack_frame import NatalStackFrame

    NatalStackFrame._keep_all_debugging = True
    yield
    NatalStackFrame._keep_all_debugging = False


@pytest.fixture
def sourcemap_debug():
    from feature_gates import FeatureGates

    previous = FeatureGates.sourcemap_debug()
    FeatureGates.set_sourcemap_debug(True)
    yield
    FeatureGates.set_sourcemap_debug(previous)


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Currently, this test only works in python 3.11 and above",
)
@pytest.mark.serial
def test_r3sourcemap(sourcemap_debug, sourcemap_enabled):
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

    assert filename == r3sm.filename
    assert str(r3sm.source_root).startswith(str(Path.cwd()))
    assert list(range(len(r3sm.entries))) == [line for line, _ in r3sm.entries]
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
        "AA4DqB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACiBrB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADjBqB;AAAA;ACiBrB;ADjBqB;AAAA;AAAA;ACiBrB;AAAA;AAAA;AAAA;ADjBqB;ACiBrB;ADjBqB;ACIrB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADJqB;AAAA;AAAA;AAAA;ACIrB;AAAA;AAAA;AAAA;AAAA;AAAA;ADJqB;ACIrB;ADJqB;ACpBrB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADoBqB;AAAA;AAAA;ACpBrB;ADoBqB;AAAA;AAAA;ACpBrB;ADoBqB;ACpBrB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ADoBqB;ACpBrB;ADoBqB;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AChDjB;AACc;AAAd;AAA4C;AAAc;AAA3B;AAA/B;AAFuB;ADiDN;AAAA;AAAA;ACtCkB;AAAA;ADsClB;AAAA;AAAA;AAAA;AAAA;ACxCiB;AAAA;AAdtC;AAAA;AAAA;AACkB;AAAgB;AAAhB;AAAP;AADX;AAkCA;AAAA;AAAA;ADoBqB;AAAA;ACPN;AAAA;AAA0B;AAAA;AAA1B;AAAP;AACO;AAAA;AAA4B;AAA5B;AAAP;AAEI;AAAA;AACA;AACa;AAAA;AAAkB;AAA/B;AAAmD;AAAA;AAAnD;AAHJ;AAfR;AAwBA;AAAA;AAAA;AASmC;AAAgB;AAA7B;AATtB;AAaA;AAAA;AAAA;ADjBqB;AAAA;ACqCT;AACA;AACa;AAAc;AAA3B;AAA+C;AAA/C;AAHJ;AAKA;AA7DR;AA8DQ;AAG2B;AAAA;AAH3B;AAIyB;AAJzB;AAKsB;AALtB;AAQA;AAjCR"
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
def test_reconstruct(sourcemap_enabled):
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
def test_feature_gate_for_frames(sourcemap_enabled):
    from feature_gates import FeatureGates

    assert FeatureGates.sourcemap_enabled() is True
    from pyteal.stack_frame import NatalStackFrame

    assert NatalStackFrame.sourcemapping_is_off() is False


def make(x, y, z):
    import pyteal as pt

    return pt.Int(x) + pt.Int(y) + pt.Int(z)


@pytest.mark.serial
def test_lots_o_indirection(sourcemap_enabled):
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
    sourcemap_enabled,
    StackFrame_keep_all_debugging,
):
    import pyteal as pt
    from pyteal.stack_frame import StackFrame

    e1 = pt.Seq(pt.Pop(make(1, 2, 3)), pt.Pop(make(4, 5, 6)), make(7, 8, 9))

    frame_infos = e1.stack_frames._frames
    last_drop_idx = 1
    assert StackFrame._frame_info_is_right_before_core(
        frame_infos[last_drop_idx].frame_info
    ), "Uh oh! Something about NatalStackFrame has changes which puts in jeopardy Source Map functionality"


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


SUCCESSFUL_SUBROUTINE_LINENO = 204


@pytest.mark.serial
def test_hybrid_w_offset(sourcemap_debug, sourcemap_enabled):
    from feature_gates import FeatureGates
    from pyteal import stack_frame

    assert FeatureGates.sourcemap_enabled() is True
    assert FeatureGates.sourcemap_debug() is True
    assert stack_frame.NatalStackFrame.sourcemapping_is_off() is False
    assert stack_frame.NatalStackFrame._debugging() is True

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
    raw_code = lbf.raw_code()
    naive_line = lbf.frame_info.lineno

    # consistent across versions:
    assert etarget == hwo[0]
    assert func_source == nsource

    # inconsistent between 3.10 and 3.11:
    if sys.version_info[:2] <= (3, 10):
        assert 0 == hwo[1]
        assert "def set_foo(" == raw_code
        assert SUCCESSFUL_SUBROUTINE_LINENO == naive_line
    else:
        assert 1 == hwo[1]
        assert "@pt.ABIReturnSubroutine" == raw_code
        assert SUCCESSFUL_SUBROUTINE_LINENO - 1 == naive_line


PyTealFrame_CASES = [
    (
        "some code",
        False,
        "some chunk",
        ("some chunk", 0),
    ),
    (
        "some code",
        True,
        "some chunk",
        ("some chunk", 0),
    ),
    (
        "first line",
        True,
        "first line and more\nsecond line",
        ("first line and more", 0),
    ),
    (
        "first line",
        True,
        "first line and more\ndef second line",
        ("def second line", 1),
    ),
    (
        "first line",
        False,
        None,
        ("first line", 0),
    ),
    (
        "first line",
        True,
        None,
        ("first line", 0),
    ),
]


@contextmanager
def patch_pt_frame(code, is_funcdef, pt_chunk):
    from pyteal.stack_frame import PyTealFrame

    node = None
    if is_funcdef:
        node = FunctionDef(name="foo", body=[], decorator_list=[], returns=None)

    frame = PyTealFrame(
        frame_info="dummy frame_info", node=node, creator=None, full_stack=None
    )
    with mock.patch.object(frame, "raw_code", return_value=code), mock.patch.object(
        frame, "node_source", return_value=pt_chunk
    ):
        yield frame


@pytest.mark.parametrize("code, is_funcdef, pt_chunk, expected", PyTealFrame_CASES)
def test_mock_hybrid_w_offset(code, is_funcdef, pt_chunk, expected):
    with patch_pt_frame(code, is_funcdef, pt_chunk) as pt_frame:
        assert expected == pt_frame._hybrid_w_offset()


def test_tabulate_args_can_be_dictified():
    from pyteal.compiler.sourcemap import _PyTealSourceMapper, TealMapItem

    tmi = TealMapItem(
        pt_frame=mock.MagicMock(),
        teal_lineno=13,
        teal_line="some teal line",
        teal_component="some teal component",
    )
    all_cols = {v: v for v in _PyTealSourceMapper._tabulate_param_defaults.values()}
    full_dict = tmi.asdict(**all_cols)
    assert set(all_cols.keys()) == set(full_dict.keys())


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
        (26, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (27, ("router._build_impl(rci)", 0)),
        (28, ("router._build_impl(rci)", 0)),
        (29, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (30, ("router._build_impl(rci)", 0)),
        (31, ("router._build_impl(rci)", 0)),
        (32, ("router._build_impl(rci)", 0)),
        (33, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (34, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (35, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (36, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (37, ("router._build_impl(rci)", 0)),
        (38, ("def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:", 1)),
        (39, ("router._build_impl(rci)", 0)),
        (40, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (41, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (42, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (43, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (44, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (45, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (46, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (47, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (48, ("router._build_impl(rci)", 0)),
        (49, ("router._build_impl(rci)", 0)),
        (50, ("router._build_impl(rci)", 0)),
        (51, ("router._build_impl(rci)", 0)),
        (52, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (53, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (54, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (55, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (56, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (57, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
        (58, ("router._build_impl(rci)", 0)),
        (59, ("def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:", 1)),
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
        (
            76,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (77, ("router._build_impl(rci)", 0)),
        (78, ("router._build_impl(rci)", 0)),
        (79, ("router._build_impl(rci)", 0)),
        (
            80,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (81, ("router._build_impl(rci)", 0)),
        (82, ("router._build_impl(rci)", 0)),
        (83, ("router._build_impl(rci)", 0)),
        (
            84,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (85, ("router._build_impl(rci)", 0)),
        (
            86,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            87,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            88,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            89,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            90,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            91,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (
            92,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
        (93, ("router._build_impl(rci)", 0)),
        (
            94,
            (
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
            ),
        ),
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
                "def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:",
                1,
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
