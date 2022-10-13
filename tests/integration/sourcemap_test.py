import ast
from configparser import ConfigParser
import json
from pathlib import Path
import time

import pytest
from unittest import mock

from algosdk.source_map import R3SourceMap, R3SourceMapJSON

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"

FIXTURES = Path.cwd() / "tests" / "integration" / "sourcemaps"


def test_frames():
    from pyteal.util import Frames

    Frames._skip_all = False

    this_file, this_func = "sourcemap_test.py", "test_frames"
    this_lineno, this_frame = 23, Frames()[1]
    code = f"    this_lineno, this_frame = {this_lineno}, Frames()[1]\n"
    this_col_offset, this_end_col_offset = 34, 42
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
    assert isinstance(node.parent, ast.Subscript)  # type: ignore


def test_SourceMapItem_source_mapping():
    from pyteal.util import Frames

    Frames._skip_all = False

    from pyteal.compiler.sourcemap import PyTealFrame, SourceMapItem
    import pyteal as pt

    expr = pt.Int(0) + pt.Int(1)
    expr_line_offset, expr_str = 51, "expr = pt.Int(0) + pt.Int(1)"

    def mock_teal(ops):
        return [f"{i+1}. {op}" for i, op in enumerate(ops)]

    ops = []
    b = expr.__teal__(pt.CompileOptions())[0]
    while b:
        ops.extend(b.ops)
        b = b.nextBlock  # type: ignore

    teals = mock_teal(ops)
    smis = [
        SourceMapItem(i + 1, teals[i], op, PyTealFrame(op.expr.frames[4]))
        for i, op in enumerate(ops)
    ]

    mock_source_lines = [""] * 500
    mock_source_lines[expr_line_offset] = expr_str
    source_files = ["sourcemap_test.py"]
    r3sm = R3SourceMap(
        file="dohhh.teal",
        source_root="~",
        entries={(i, 0): smi.source_mapping() for i, smi in enumerate(smis)},
        index=[(0,) for _ in range(3)],
        file_lines=list(map(lambda x: x.teal, smis)),
        source_files=source_files,
        source_files_lines=[mock_source_lines],
    )
    expected_json = '{"version": 3, "sources": ["tests/integration/sourcemap_test.py"], "names": [], "mappings": "AAkDW;AAAY;AAAZ", "file": "dohhh.teal", "sourceRoot": "~"}'

    assert expected_json == json.dumps(r3sm.to_json())

    r3sm_unmarshalled = R3SourceMap.from_json(
        R3SourceMapJSON(**json.loads(expected_json)),
        sources_content_override=["\n".join(mock_source_lines)],
        target="\n".join(teals),
    )

    # TODO: test various properties of r3sm_unmarshalled

    assert expected_json == json.dumps(r3sm_unmarshalled.to_json())


"""
# TODO: Additional examples needed before merging:

1. Inline programs patched together from various sources
2. Example with OpUp
3. Run on the ABI Router example
4. Run on Steve's Staking Contract
5. Run an Ben's AMM

?. Beaker example

"""


def no_regressions():
    from pyteal import OptimizeOptions
    from examples.application.abi.algobank import router

    approval, clear, contract = router.compile_program(
        version=6, optimize=OptimizeOptions(scratch_slots=True)
    )

    with open(ALGOBANK / "algobank_approval.teal") as af:
        assert approval == af.read()

    with open(ALGOBANK / "algobank_clear_state.teal") as cf:
        assert clear == cf.read()

    with open(ALGOBANK / "algobank.json") as jf:
        assert json.dumps(contract.dictify(), indent=4) == jf.read()


def test_no_regression_with_sourcemap_as_configured():
    no_regressions()


def test_no_regression_with_sourcemap_enabled():
    from pyteal.util import Frames

    Frames._skip_all = False

    no_regressions()


def test_no_regression_with_sourcemap_disabled():
    from pyteal.util import Frames

    Frames._skip_all = True

    no_regressions()


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
    with open(FIXTURES / f"{name}", "w") as f:
        f.write(new_version)

    not_actually_comparing = True
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


def test_PyTealSourceMap_R3SourceMap_roundtrip():
    assert False, "test is currently RED"


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


def test_sourcemap_fails_because_unconfigured():
    from pyteal import OptimizeOptions
    from pyteal.compiler.sourcemap import SourceMapDisabledError

    from examples.application.abi.algobank import router

    with pytest.raises(SourceMapDisabledError) as smde:
        router.compile_program_with_sourcemaps(
            version=6,
            optimize=OptimizeOptions(scratch_slots=True),
        )

    assert "pyteal.ini" in str(smde.value)


@mock.patch.object(ConfigParser, "getboolean", side_effect=Exception("1337"))
def test_sourcemap_fails_elegantly_when_no_ini(_):
    from pyteal import OptimizeOptions
    from pyteal.compiler.sourcemap import SourceMapDisabledError

    from examples.application.abi.algobank import router

    with pytest.raises(SourceMapDisabledError) as smde:
        router.compile_program_with_sourcemaps(
            version=6,
            optimize=OptimizeOptions(scratch_slots=True),
        )

    assert "pyteal.ini" in str(smde.value)


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
    from pyteal import OptimizeOptions

    from examples.application.abi.algobank import router

    router.compile_program(version=6, optimize=OptimizeOptions(scratch_slots=True))


def source_map_compilation():
    from pyteal import OptimizeOptions

    from examples.application.abi.algobank import router

    router.compile_program_with_sourcemaps(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
    )


def annotated_teal():
    from pyteal import OptimizeOptions

    from examples.application.abi.algobank import router

    router.compile_program_with_sourcemaps(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
    ).approval_sourcemap.annotated_teal(unparse_hybrid=True)


def test_profile():
    """
    TODO: run factory(simple_compilation, skip=???) through a memory profiler
    """

    def factory(func, skip):
        def trial():
            if skip:
                Frames.skip = True
            trials, tot = time_for_n_secs(simple_compilation, 10)
            avg = tot / len(trials)
            N = len(trials)
            print("\n" + f"{func.__name__}: {avg=}, {N=}")

            Frames.skip = False

        return trial

    # profile.run("factory(simple_compilation, skip=True)")


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


@pytest.mark.skip()
def test_time_benchmark_under_config():
    from pyteal.util import Frames

    print(f"{Frames.skipping_all()=}")

    trial(simple_compilation)
    trial(simple_compilation)

    assert False


"""RESULTS FROM test_time_benchmark_under_config()
Frames.skipping_all()=True
simple_compilation: avg=0.020052342233294714, N=499
simple_compilation: avg=0.020396863370223346, N=491
"""


@pytest.mark.skip()
@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_time_benchmark_sourcemap_enabled(_):
    """
    UPSHOT: expect deterioration of (5 to 15)X when enabling source maps.
    """
    from pyteal.util import Frames

    print(f"{Frames.skipping_all()=}")

    trial(simple_compilation)
    trial(simple_compilation)

    trial(source_map_compilation)
    trial(source_map_compilation)

    trial(annotated_teal)
    trial(annotated_teal)

    assert False


"""RESULTS FROM test_time_benchmark_sourcemap_enabled
Frames.skipping_all()=False
simple_compilation: avg=0.2972649405984318, N=34  <---- FIRST RUN RESULT CAN PROBLY BE DISCARDED
simple_compilation: avg=0.11990405832018171, N=84
source_map_compilation: avg=0.11482023921879855, N=88
source_map_compilation: avg=0.11954815898622785, N=84
annotated_teal: avg=0.11837509379667395, N=85
annotated_teal: avg=0.11272530341416262, N=89
"""


def test_config():
    from pyteal.util import Frames

    config = ConfigParser()
    config.read([".flake8", "mypy.ini", "pyteal.ini"])

    assert [
        "flake8",
        "mypy",
        "mypy-semantic_version.*",
        "mypy-pytest.*",
        "mypy-algosdk.*",
        "pyteal",
        "pyteal-source-mapper",
    ] == config.sections()

    assert ["ignore", "per-file-ignores", "ban-relative-imports"] == config.options(
        "flake8"
    )

    assert ["enabled"] == config.options("pyteal-source-mapper")

    assert config.getboolean("pyteal-source-mapper", "enabled") is False
    assert Frames.skipping_all() is True

    Frames._skip_all = False
    assert Frames.skipping_all() is False
    assert Frames.skipping_all(_force_refresh=True) is True


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_mocked_config_for_frames(_):
    config = ConfigParser()
    assert config.getboolean("pyteal-source-mapper", "enabled") is True
    from pyteal.util import Frames

    assert Frames.skipping_all() is False
    assert Frames.skipping_all(_force_refresh=True) is False
