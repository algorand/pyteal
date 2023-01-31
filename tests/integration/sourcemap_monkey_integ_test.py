from configparser import ConfigParser
from unittest import mock

import pytest

"""
This file monkey-patches ConfigParser in order to enable source mapping
and test the results of source mapping various PyTeal dapps.
"""

from importlib import import_module
from pathlib import Path

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


@pytest.mark.serial("headers")
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


# --- scratch --- #
