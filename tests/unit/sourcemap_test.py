"""
This test would typically reside right next to `pyteal/compiler/sourcemap.py`.
However, since the path `pyteal/compiler` is on the StackFrame._internal_paths
blacklist, we need to move the test elsewhere to obtain reliable results.
"""

import ast
import json
from pathlib import Path
import time
from unittest import mock

import pytest

from pyteal.compiler.sourcemap import R3SourceMap, R3SourceMapJSON

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"


@pytest.fixture
def StackFrame_keep_all_debugging():
    from pyteal.stack_frame import NatalStackFrame

    NatalStackFrame._keep_all_debugging = True
    yield
    NatalStackFrame._keep_all_debugging = False


@pytest.fixture
def sourcemap_enabled():
    from feature_gates import FeatureGates

    previous = FeatureGates.sourcemap_enabled()
    FeatureGates.set_sourcemap_enabled(True)
    yield
    FeatureGates.set_sourcemap_enabled(previous)


@pytest.fixture
def sourcemap_disabled():
    from feature_gates import FeatureGates

    previous = FeatureGates.sourcemap_enabled()
    FeatureGates.set_sourcemap_enabled(False)
    yield
    FeatureGates.set_sourcemap_enabled(previous)


@pytest.mark.serial
def test_frames(sourcemap_enabled, StackFrame_keep_all_debugging):
    from pyteal.stack_frame import NatalStackFrame

    assert NatalStackFrame.sourcemapping_is_off() is False

    this_file, this_func = "sourcemap_test.py", "test_frames"
    this_lineno, this_frame = 56, NatalStackFrame()._frames[1]
    code = (
        f"    this_lineno, this_frame = {this_lineno}, NatalStackFrame()._frames[1]\n"
    )
    this_col_offset, this_end_col_offset = 34, 51
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
    assert isinstance(node.parent, ast.Attribute)  # type: ignore
    assert isinstance(node.parent.parent, ast.Subscript)  # type: ignore


@pytest.mark.serial
def test_TealMapItem_source_mapping(sourcemap_enabled):
    from pyteal.stack_frame import NatalStackFrame

    assert NatalStackFrame.sourcemapping_is_off() is False

    import pyteal as pt
    from pyteal.compiler.sourcemap import TealMapItem

    expr = pt.Int(0) + pt.Int(1)
    expr_line_offset, expr_str = 50, "expr = pt.Int(0) + pt.Int(1)"

    def mock_teal(ops):
        return [f"{i+1}. {op}" for i, op in enumerate(ops)]

    components = []
    b = expr.__teal__(pt.CompileOptions())[0]
    while b:
        components.extend(b.ops)
        b = b.nextBlock  # type: ignore

    teals = mock_teal(components)
    tmis = [
        TealMapItem(op.expr.stack_frames._frames[0].as_pyteal_frame(), i, teals[i], op)
        for i, op in enumerate(components)
    ]

    mock_source_lines = [""] * 500
    mock_source_lines[expr_line_offset] = expr_str
    source_files = ["sourcemap_test.py"]
    r3sm = R3SourceMap(
        filename="dohhh.teal",
        source_root="~",
        entries={(i, 0): tmi.source_mapping() for i, tmi in enumerate(tmis)},
        index=[(0,) for _ in range(3)],
        file_lines=list(map(lambda x: x.teal_line, tmis)),
        source_files=source_files,
        source_files_lines=[mock_source_lines],
    )
    expected_json = '{"version": 3, "sources": ["tests/unit/sourcemap_test.py"], "names": [], "mappings": "AAuFW;AAAY;AAAZ", "file": "dohhh.teal", "sourceRoot": "~"}'

    assert expected_json == json.dumps(r3sm.to_json())

    r3sm_unmarshalled = R3SourceMap.from_json(
        R3SourceMapJSON(**json.loads(expected_json)),  # type: ignore
        sources_content_override=["\n".join(mock_source_lines)],
        target="\n".join(teals),
    )

    # TODO: test various properties of r3sm_unmarshalled

    assert expected_json == json.dumps(r3sm_unmarshalled.to_json())


def compare_and_assert(file, actual):
    with open(file, "r") as f:
        expected_lines = f.read().splitlines()
        actual_lines = actual.splitlines()
        assert len(expected_lines) == len(actual_lines)
        assert expected_lines == actual_lines


def no_regressions_algobank():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    approval, clear, contract = router.compile_program(
        version=6, optimize=OptimizeOptions(scratch_slots=True)
    )

    compare_and_assert(
        ALGOBANK / "algobank.json", json.dumps(contract.dictify(), indent=4)
    )
    compare_and_assert(ALGOBANK / "algobank_clear_state.teal", clear)
    compare_and_assert(ALGOBANK / "algobank_approval.teal", approval)


@pytest.mark.serial
def test_no_regression_with_sourcemap_as_configured_algobank():
    no_regressions_algobank()


@pytest.mark.serial
def test_no_regression_with_sourcemap_enabled_algobank(sourcemap_enabled):
    from pyteal.stack_frame import NatalStackFrame

    assert NatalStackFrame.sourcemapping_is_off() is False
    no_regressions_algobank()


@pytest.mark.serial
def test_no_regression_with_sourcemap_disabled_algobank(sourcemap_disabled):
    from pyteal.stack_frame import NatalStackFrame

    assert NatalStackFrame.sourcemapping_is_off() is True

    no_regressions_algobank()


@pytest.mark.serial
def test_sourcemap_fails_because_not_enabled():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions
    from pyteal.errors import SourceMapDisabledError

    with pytest.raises(SourceMapDisabledError) as smde:
        router.compile(
            version=6,
            optimize=OptimizeOptions(scratch_slots=True),
            with_sourcemaps=True,
        )

    assert """Cannot calculate Teal to PyTeal source map because stack frame discovery is turned off.

    To enable source maps: import `from feature_gates import FeatureGates` and call `FeatureGates.set_sourcemap_enabled(True)`.""" in str(
        smde.value
    )


def test_PyTealSourceMapper_validate_build_annotate():
    from pyteal import TealInternalError
    from pyteal.compiler.sourcemap import _PyTealSourceMapper

    # --- CONSTRUCTOR VALIDATIONS --- #
    match = "Please provide non-empty teal_chunks"
    with pytest.raises(TealInternalError, match=match):
        _PyTealSourceMapper([], [], build=False, annotate_teal=False)

    match = "Please provide non-empty components"
    with pytest.raises(TealInternalError, match=match):
        _PyTealSourceMapper(["a chunk"], [], build=False, annotate_teal=False)

    # --- BUILD VALIDATIONS --- #
    ptsm = _PyTealSourceMapper(
        ["a chunk"], ["a component", "another"], build=False, annotate_teal=False
    )

    def full_match(s):
        return f"""{s}
        {_PyTealSourceMapper.UNEXPECTED_ERROR_SUFFIX}"""

    match = full_match(
        r"expected same number of teal chunks \(1\) and components \(2\)"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm.build()

    ptsm.teal_chunks = ptsm.components = []
    match = full_match("cannot generate empty source map: no components")
    with pytest.raises(TealInternalError, match=match):
        ptsm.build()

    teal_chunks = ["first line\nsecond line", "third line\nfourth line\nfifth line"]
    teal = [
        "first line",
        "second line",
        "third line",
        "fourth line",
        "fifth line",
    ]
    i = 0
    for chunk in teal_chunks:
        for line in chunk.splitlines():
            assert teal[i] == line
            i += 1

    def mock_TealMapItem(s):
        tmi = mock.Mock()
        tmi.teal_line = s
        return tmi

    def mock_R3SourceMap(lines):
        r3sm = mock.Mock()
        r3sm.file_lines = lines
        return r3sm

    ptsm.teal_chunks = teal_chunks
    ptsm._cached_tmis = [mock_TealMapItem(s) for s in teal]
    ptsm._cached_r3sourcemap = mock_R3SourceMap(teal)

    ptsm._validate_build()
    ptsm.teal_chunks.append("sixth line")
    match = full_match(
        r"teal chunks has 6 teal lines which doesn't match the number of cached TealMapItem's \(5\)"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_build()

    ptsm._cached_tmis.append(mock_TealMapItem("sixth line"))
    ptsm._cached_r3sourcemap.file_lines.append("sixth line")
    ptsm._validate_build()

    match = full_match(
        r"teal chunks has 6 teal lines which doesn't match the number of cached TealMapItem's \(7\)"
    )
    ptsm._cached_tmis.append(mock_TealMapItem("seventh line"))
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_build()

    del ptsm._cached_tmis[-1]
    ptsm._validate_build()

    ptsm._cached_tmis[-1] = mock_TealMapItem("NOT the sixth line")
    match = full_match(
        r"teal chunk lines don't match TealMapItem's at index 5. \('sixth line' v. 'NOT the sixth line'\)"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_build()

    ptsm._cached_tmis[-1] = mock_TealMapItem("sixth line")
    ptsm._validate_build()

    ptsm._cached_r3sourcemap.file_lines.append("seventh line")
    match = full_match(
        r"there are 6 TealMapItem's which doesn't match the number of file_lines in the cached R3SourceMap \(7\)"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_build()

    del ptsm._cached_r3sourcemap.file_lines[-1]
    ptsm._validate_build()

    ptsm._cached_r3sourcemap.file_lines[-1] = "NOT the sixth line"
    match = full_match(
        r"TealMapItem's don't match R3SourceMap.file_lines at index 5. \('sixth line' v. 'NOT the sixth line'\)"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_build()

    ptsm._cached_r3sourcemap.file_lines[-1] = "sixth line"
    ptsm._validate_build()

    # --- ANNOTATE VALIDATIONS --- #
    annotated = [f"{teal}   // some other stuff{i}" for i, teal in enumerate(teal)]
    omit_headers = True
    ptsm._validate_annotated(omit_headers, teal, annotated)

    omit_headers = False
    match = full_match(
        r"mismatch between count of teal_lines \(6\) and annotated_lines \(6\) for the case omit_headers=False"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_annotated(omit_headers, teal, annotated)

    annotated_w_headers = ["// some header"] + annotated
    ptsm._validate_annotated(omit_headers, teal, annotated_w_headers)

    omit_headers = True
    match = full_match(
        r"mismatch between count of teal_lines \(6\) and annotated_lines \(7\) for the case omit_headers=True"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_annotated(omit_headers, teal, annotated_w_headers)

    annotated_3 = annotated[3]
    annotated[3] = "doesn't begin with the teal line"
    match = full_match(
        r"annotated teal ought to begin exactly with the teal line but line 4 \[doesn't begin with the teal line\] doesn't start with \[fourth line\]"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_annotated(omit_headers, teal, annotated)

    annotated[3] = annotated_3
    ptsm._validate_annotated(omit_headers, teal, annotated)

    annotated_w_headers[4] = "doesn't begin with the teal line"
    omit_headers = False
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_annotated(omit_headers, teal, annotated_w_headers)

    annotated_w_headers[4] = annotated_3
    ptsm._validate_annotated(omit_headers, teal, annotated_w_headers)

    omit_headers = True
    annotated_2 = annotated[2]
    annotated[2] = f"{teal[2]}   some other stuff not all // commented out"
    match = full_match(
        rf"annotated teal ought to begin exactly with the teal line followed by annotation in comments but line 3 \[{annotated[2]}\] has non-commented out annotations"
    )
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_annotated(omit_headers, teal, annotated)

    annotated[2] = annotated_2
    ptsm._validate_annotated(omit_headers, teal, annotated)

    omit_headers = False
    annotated_w_headers[3] = f"{teal[2]}   some other stuff not all // commented out"
    with pytest.raises(TealInternalError, match=match):
        ptsm._validate_annotated(omit_headers, teal, annotated_w_headers)

    annotated_w_headers[3] = annotated_2
    ptsm._validate_annotated(omit_headers, teal, annotated_w_headers)

    # --- ANNOTATE VALIDATIONS - SPECIAL CASE --- #
    meth_sig = "deposit(pay,account)void"
    special = f"method {meth_sig}      //    (30)"
    teal.append(special)
    annotated_w_headers.append(special)
    ptsm._validate_annotated(omit_headers, teal, annotated_w_headers)


def test_examples_sourcemap():
    """
    Test to ensure that examples/application/teal/sourcemap.py doesn't go stale
    """
    from examples.application.sourcemap import Compilation, Mode, program

    examples = Path.cwd() / "examples" / "application" / "teal"

    approval_program = program()

    results = Compilation(approval_program, mode=Mode.Application, version=8).compile(
        with_sourcemap=True, annotate_teal=True, annotate_teal_headers=True
    )

    teal = examples / "sourcemap.teal"
    annotated = examples / "sourcemap_annotated.teal"

    with open(teal) as f:
        assert f.read() == results.teal

    with open(annotated) as f:
        fixture = f.read().splitlines()
        annotated = results.sourcemap.annotated_teal.splitlines()
        for i, (f, a) in enumerate(zip(fixture, annotated)):
            f_cols = f.split()
            a_cols = a.split()
            if f_cols == a_cols:
                continue

            if f_cols[-1] == "annotate_teal_headers=True)":
                assert f_cols[:2] == a_cols[:2], f"index {i} doesn't match"
                assert f_cols[-4:] == a_cols[-4:], f"index {i} doesn't match"
                continue

            # must differ because fixture repeats PYTEAL PATH so omits it
            assert len(f_cols) == len(a_cols) - 1, f"index {i} doesn't match"

            a_comment = a_cols.index("//")
            assert f_cols == (
                a_cols[: a_comment + 1] + a_cols[a_comment + 2 :]
            ), f"index {i} doesn't match"


@pytest.mark.skip(
    reason="""Supressing this flaky test as 
router_test::test_router_compile_program_idempotence is similar in its goals
and we expect flakiness to persist until https://github.com/algorand/pyteal/issues/199
is finally addressed """
)
@pytest.mark.serial
def test_idempotent():
    # make sure we get clean up properly and therefore get idempotent results
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    approval1, clear1, contract1 = (
        func := lambda: router.compile_program(
            version=6, optimize=OptimizeOptions(scratch_slots=True)
        )
    )()
    approval2, clear2, contract2 = func()

    assert contract1.dictify() == contract2.dictify()
    assert len(clear1.splitlines()) == len(clear2.splitlines())
    assert clear1 == clear2
    assert len(approval1.splitlines()) == len(approval2.splitlines())
    assert approval1 == approval2


# ---- BENCHMARKS - SKIPPED BY DEFAULT ---- #


def time_for_n_secs(f, n):
    start = time.time()

    def since():
        return time.time() - start

    total_time = 0.0
    snapshots = [0.0]
    while total_time < n:
        f()
        total_time = since()
        snapshots.append(total_time)

    trials = [snapshots[i + 1] - s for i, s in enumerate(snapshots[:-1])]
    return trials, total_time


def simple_compilation():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    router.compile_program(version=6, optimize=OptimizeOptions(scratch_slots=True))


def source_map_compilation():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    router.compile(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        with_sourcemaps=True,
    )


def annotated_teal():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    compilation = router.compile(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        with_sourcemaps=True,
    )

    assert compilation.approval_sourcemapper

    return compilation.approval_sourcemapper.annotated_teal()


summaries_only = True


def trial(func):
    trials, tot = time_for_n_secs(simple_compilation, 10)
    avg = tot / len(trials)
    N = len(trials)
    trials = "" if summaries_only else f"{trials=}"
    print(
        f"""
{func.__name__}: {avg=}, {N=}
{trials}"""
    )


@pytest.mark.skip(reason="Benchmarks are too slow to run every time")
@pytest.mark.serial
def test_time_benchmark_with_default_feature_gates():
    from pyteal.stack_frame import NatalStackFrame

    print(f"{NatalStackFrame.sourcemapping_is_off()=}")

    trial(simple_compilation)
    trial(simple_compilation)

    assert False


@pytest.mark.skip(reason="Benchmarks are too slow to run every time")
@pytest.mark.serial
def test_time_benchmark_sourcemap_enabled(sourcemap_enabled):
    """
    UPSHOT: expect deterioration of (5 to 15)X when enabling source maps.
    """
    from pyteal.stack_frame import NatalStackFrame

    print(f"{NatalStackFrame.sourcemapping_is_off()=}")
    print(
        """
keep_all: bool = True,
stop_after_first_pyteal: bool = True,
keep_one_frame_only: bool = True,
"""
    )

    trial(simple_compilation)
    trial(simple_compilation)

    trial(source_map_compilation)
    trial(source_map_compilation)

    trial(annotated_teal)
    trial(annotated_teal)

    assert False
