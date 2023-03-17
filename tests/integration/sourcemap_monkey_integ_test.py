from importlib import import_module
from itertools import product
from pathlib import Path

import pytest

from feature_gates import FeatureGates

"""
Tests run with a fixture that enables the sourcemap
via feature gate.
"""


STABLE_SLOT_GENERATION = (
    False  # The second router is flaky due to issue 199, so skipping for now
)
FIXTURES = Path.cwd() / "tests" / "integration" / "teal" / "annotated"

ROUTERS = [
    ("examples.application.abi.algobank", "router"),
    ("pyteal.compiler.compiler_test", "FIRST_ROUTER"),
]

if not STABLE_SLOT_GENERATION:
    del ROUTERS[1]


@pytest.fixture
def sourcemap_enabled():
    previous = FeatureGates.sourcemap_enabled()
    FeatureGates.set_sourcemap_enabled(True)
    yield
    FeatureGates.set_sourcemap_enabled(previous)


@pytest.mark.skipif(not STABLE_SLOT_GENERATION, reason="cf. #199")
@pytest.mark.serial
@pytest.mark.parametrize("path, obj", ROUTERS)
@pytest.mark.parametrize("annotate_teal_headers", [True, False])
@pytest.mark.parametrize("annotate_teal_concise", [True, False])
def test_sourcemap_annotate(
    sourcemap_enabled, path, obj, annotate_teal_headers, annotate_teal_concise
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

    CL = 50  # COMPILATION LINE right before this
    CFILE = "tests/integration/sourcemap_monkey_integ_test.py"  # this file
    COMPILE = "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), assemble_constants=False, with_sourcemaps=True, approval_filename=a_fname, clear_filename=c_fname, pcs_in_sourcemap=True, annotate_teal=True, annotate_teal_headers=annotate_teal_headers, annotate_teal_concise=annotate_teal_concise)"
    BCAs = "BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL))"
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
        BCAs=BCAs,
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


@pytest.mark.skipif(not STABLE_SLOT_GENERATION, reason="cf. #199")
@pytest.mark.serial
def test_no_regressions_via_fixtures_algobank(sourcemap_enabled):
    import pyteal as pt

    module_path, obj = ROUTERS[0]
    algobank_router = getattr(import_module(module_path), obj)
    assert algobank_router.name == "AlgoBank"

    first_approval, first_clear, _ = algobank_router.compile_program(
        version=6, optimize=pt.OptimizeOptions(scratch_slots=True)
    )

    algobank_path = Path.cwd() / "examples" / "application" / "abi"

    with open(algobank_path / "algobank_approval.teal") as f:
        expected_approval = f.read()

    with open(algobank_path / "algobank_clear_state.teal") as f:
        expected_clear = f.read()

    assert expected_approval == first_approval
    assert expected_clear == first_clear

    bundle = algobank_router.compile(
        version=6,
        optimize=pt.OptimizeOptions(scratch_slots=True),
    )
    assert expected_approval == bundle.approval_teal
    assert expected_clear == bundle.clear_teal

    assert first_approval == bundle.approval_teal
    assert first_clear == bundle.clear_teal

    assert bundle.approval_sourcemap is None
    assert bundle.clear_sourcemap is None

    expected_approval_prefixes = expected_approval.splitlines()
    expected_clear_prefixes = expected_clear.splitlines()

    first_approval_prefixes = first_approval.splitlines()
    first_clear_prefixes = first_clear.splitlines()

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

        current_approval_lines = bundle.approval_sourcemap.annotated_teal.splitlines()
        current_clear_lines = bundle.clear_sourcemap.annotated_teal.splitlines()

        if headers:
            del current_approval_lines[0]
            del current_clear_lines[0]

        assert_lines_start_with(expected_approval_prefixes, current_approval_lines)
        assert_lines_start_with(expected_clear_prefixes, current_clear_lines)
        assert_lines_start_with(first_approval_prefixes, current_approval_lines)
        assert_lines_start_with(first_clear_prefixes, current_clear_lines)

    for pcs, headers, concise in product([True, False], repeat=3):
        assert_didnt_regress(pcs, headers, concise)


RPS = Path.cwd() / "tests" / "teal"


@pytest.mark.serial
def test_no_regressions_via_fixtures_rps(sourcemap_enabled):
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
