from configparser import ConfigParser
from importlib import import_module
from itertools import product
from pathlib import Path
from unittest import mock

import pytest

"""
This file monkey-patches ConfigParser in order to enable source mapping
and test the results of source mapping various PyTeal dapps.
"""


BRUTE_FORCE_TERRIBLE_SKIPPING = (
    """The second router is flaky due to issue 199, so skipping for now"""
)
FIXTURES = Path.cwd() / "tests" / "integration" / "teal" / "annotated"

ROUTERS = [
    ("examples.application.abi.algobank", "router"),
    ("pyteal.compiler.compiler_test", "FIRST_ROUTER"),
]

if BRUTE_FORCE_TERRIBLE_SKIPPING:
    del ROUTERS[1]


@pytest.fixture
def mock_ConfigParser():
    patcher = mock.patch.object(ConfigParser, "getboolean", return_value=True)
    patcher.start()
    yield
    patcher.stop()


@pytest.mark.serial
@pytest.mark.parametrize("path, obj", ROUTERS)
@pytest.mark.parametrize("annotate_teal_headers", [True, False])
@pytest.mark.parametrize("annotate_teal_concise", [True, False])
def test_sourcemap_annotate(
    mock_ConfigParser, path, obj, annotate_teal_headers, annotate_teal_concise
):
    from pyteal import OptimizeOptions

    router = getattr(import_module(path), obj)

    a_fname, c_fname = "A.teal", "C.teal"
    compile_bundle = router.compile(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        assemble_constants=False,
        with_sourcemaps=True,
        approval_filename=a_fname,
        clear_filename=c_fname,
        pcs_in_sourcemap=True,
        annotate_teal=True,
        annotate_teal_headers=annotate_teal_headers,
        annotate_teal_concise=annotate_teal_concise,
    )

    CL = 49  # COMPILATION LINE right before this
    CFILE = "tests/integration/sourcemap_monkey_integ_test.py"  # this file
    COMPILE = "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), assemble_constants=False, with_sourcemaps=True, approval_filename=a_fname, clear_filename=c_fname, pcs_in_sourcemap=True, annotate_teal=True, annotate_teal_headers=annotate_teal_headers, annotate_teal_concise=annotate_teal_concise)"
    INNERTXN = "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})"

    with_headers_int = int(annotate_teal_headers)
    concise_int = int(annotate_teal_concise)
    with open(
        FIXTURES / f"{router.name}_h{with_headers_int}_c{concise_int}.tealf"
    ) as f:
        tealf = f.read()

    # less confident that this annotated teal will remain identical in 310, but for now it's working:
    EXPECTED_ANNOTATED_TEAL_311 = tealf.format(
        CFILE=CFILE,
        CL=CL,
        COMPILE=COMPILE,
        INNERTXN=INNERTXN,
    ).strip()

    annotated_approval, annotated_clear = (
        compile_bundle.approval_sourcemap.annotated_teal,
        compile_bundle.clear_sourcemap.annotated_teal,
    )
    assert annotated_approval
    assert annotated_clear

    the_same = EXPECTED_ANNOTATED_TEAL_311 == annotated_approval
    print(f"{annotated_approval.splitlines()=}")
    assert the_same, first_diff(EXPECTED_ANNOTATED_TEAL_311, annotated_approval)

    raw_approval_lines, raw_clear_lines = (
        compile_bundle.approval_teal.splitlines(),
        compile_bundle.clear_teal.splitlines(),
    )

    ann_approval_lines, ann_clear_lines = (
        annotated_approval.splitlines(),
        annotated_clear.splitlines(),
    )

    assert len(raw_approval_lines) + with_headers_int == len(ann_approval_lines)
    assert len(raw_clear_lines) + with_headers_int == len(ann_clear_lines)

    for i, raw_line in enumerate(raw_approval_lines):
        assert ann_approval_lines[i + with_headers_int].startswith(raw_line)

    for i, raw_line in enumerate(raw_clear_lines):
        assert ann_clear_lines[i + with_headers_int].startswith(raw_line)


def first_diff(expected, actual):
    alines = actual.splitlines()
    elines = expected.splitlines()
    for i, e in enumerate(elines):
        if i >= len(alines):
            return f"""LINE[{i+1}] missing from actual:
{e}"""
        if e != (a := alines[i]):
            return f"""LINE[{i+1}]
{e}
VS.
{a}
"""
    if len(alines) > len(elines):
        return f"""LINE[{len(elines) + 1}] missing from expected:
{alines[len(elines)]}"""

    return ""


def assert_lines_start_with(prefixes, lines):
    assert len(prefixes) == len(lines)
    for prefix, line in zip(prefixes, lines):
        assert line.startswith(prefix)


@pytest.mark.serial
def test_no_regressions_via_fixtures_algobank(mock_ConfigParser):
    import pyteal as pt

    module_path, obj = ROUTERS[0]
    algobank_router = getattr(import_module(module_path), obj)
    assert algobank_router.name == "AlgoBank"

    actual_approval, actual_clear, _ = algobank_router.compile_program(
        version=6, optimize=pt.OptimizeOptions(scratch_slots=True)
    )

    algobank_path = Path.cwd() / "examples" / "application" / "abi"

    with open(algobank_path / "algobank_approval.teal") as f:
        expected_approval = f.read()

    with open(algobank_path / "algobank_clear_state.teal") as f:
        expected_clear = f.read()

    assert expected_approval == actual_approval
    assert expected_clear == actual_clear

    bundle = algobank_router.compile(
        version=6,
        optimize=pt.OptimizeOptions(scratch_slots=True),
    )
    assert expected_approval == bundle.approval_teal
    assert expected_clear == bundle.clear_teal

    assert bundle.approval_sourcemap is None
    assert bundle.clear_sourcemap is None

    approval_prefixes = expected_approval.splitlines()
    clear_prefixes = expected_clear.splitlines()

    def assert_didnt_regress(pcs, headers, concise):
        bundle = algobank_router.compile(
            version=6,
            optimize=pt.OptimizeOptions(scratch_slots=True),
            with_sourcemaps=True,
            pcs_in_sourcemap=pcs,
            annotate_teal=True,
            annotate_teal_headers=headers,
            annotate_teal_concise=concise,
        )
        assert expected_approval == bundle.approval_teal
        assert expected_clear == bundle.clear_teal

        actual_approval_lines = bundle.approval_sourcemap.annotated_teal.splitlines()
        actual_clear_lines = bundle.clear_sourcemap.annotated_teal.splitlines()

        if headers:
            del actual_approval_lines[0]
            del actual_clear_lines[0]

        assert_lines_start_with(approval_prefixes, actual_approval_lines)
        assert_lines_start_with(clear_prefixes, actual_clear_lines)

    for pcs, headers, concise in product([True, False], repeat=3):
        assert_didnt_regress(pcs, headers, concise)


RPS = Path.cwd() / "tests" / "teal"


@pytest.mark.serial
def test_no_regressions_via_fixtures_rps(mock_ConfigParser):
    import pyteal as pt
    from tests.teal.rps import approval_program

    actual_approval = pt.compileTeal(approval_program(), pt.Mode.Application, version=6)

    with open(RPS / "rps.teal") as f:
        expected_approval = f.read()

    assert expected_approval == actual_approval

    compilation = pt.Compilation(approval_program(), pt.Mode.Application, version=6)

    bundle = compilation.compile()

    assert expected_approval == bundle.teal

    assert bundle.sourcemap is None

    approval_prefixes = expected_approval.splitlines()

    def assert_didnt_regress(pcs, headers, concise):
        bundle = compilation.compile(
            with_sourcemap=True,
            pcs_in_sourcemap=pcs,
            annotate_teal=True,
            annotate_teal_headers=headers,
            annotate_teal_concise=concise,
        )
        assert expected_approval == bundle.teal

        actual_approval_lines = bundle.sourcemap.annotated_teal.splitlines()

        if headers:
            del actual_approval_lines[0]

        assert_lines_start_with(approval_prefixes, actual_approval_lines)

    for pcs, headers, concise in product([True, False], repeat=3):
        assert_didnt_regress(pcs, headers, concise)
