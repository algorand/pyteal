"""
This test would typically reside right next to `pyteal/compiler/sourcemap.py`.
However, since the path `pyteal/compiler` is on the StackFrame._internal_paths
blacklist, we need to move the test elsewhere to get reliable results.
"""

import ast
import json
import time
from configparser import ConfigParser
from pathlib import Path
from unittest import mock

import pytest

from pyteal.compiler.sourcemap import R3SourceMap, R3SourceMapJSON

ALGOBANK = Path.cwd() / "examples" / "application" / "abi"


@pytest.mark.serial
def test_frames():
    from pyteal.stack_frame import StackFrames

    StackFrames._no_stackframes = False

    this_file, this_func = "sourcemap_test.py", "test_frames"
    this_lineno, this_frame = 28, StackFrames(keep_all=True)[1]
    code = (
        f"    this_lineno, this_frame = {this_lineno}, StackFrames(keep_all=True)[1]\n"
    )
    this_col_offset, this_end_col_offset = 34, 60
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


@pytest.mark.serial
def test_SourceMapItem_source_mapping():
    from pyteal.stack_frame import StackFrames

    StackFrames._no_stackframes = False

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
        TealMapItem(op.expr.stack_frames[0].as_pyteal_frame(), i, teals[i], op)
        for i, op in enumerate(components)
    ]

    mock_source_lines = [""] * 500
    mock_source_lines[expr_line_offset] = expr_str
    source_files = ["sourcemap_test.py"]
    r3sm = R3SourceMap(
        file="dohhh.teal",
        source_root="~",
        entries={(i, 0): tmi.source_mapping() for i, tmi in enumerate(tmis)},
        index=[(0,) for _ in range(3)],
        file_lines=list(map(lambda x: x.teal_line, tmis)),
        source_files=source_files,
        source_files_lines=[mock_source_lines],
    )
    expected_json = '{"version": 3, "sources": ["tests/unit/sourcemap_test.py"], "names": [], "mappings": "AA0DW;AAAY;AAAZ", "file": "dohhh.teal", "sourceRoot": "~"}'

    assert expected_json == json.dumps(r3sm.to_json())

    r3sm_unmarshalled = R3SourceMap.from_json(
        R3SourceMapJSON(**json.loads(expected_json)),  # type: ignore
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
5. Run an Ben's AMM (Beaker)

"""


def no_regressions():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    approval, clear, contract = router.compile_program(
        version=6, optimize=OptimizeOptions(scratch_slots=True)
    )

    def compare_and_assert(file, actual):
        with open(ALGOBANK / file, "r") as f:
            expected_lines = f.read().splitlines()
            actual_lines = actual.splitlines()
            assert len(expected_lines) == len(actual_lines)
            assert expected_lines == actual_lines

    compare_and_assert("algobank.json", json.dumps(contract.dictify(), indent=4))
    compare_and_assert("algobank_clear_state.teal", clear)
    compare_and_assert("algobank_approval.teal", approval)


@pytest.mark.serial
def test_no_regression_with_sourcemap_as_configured():
    no_regressions()


@pytest.mark.serial
def test_no_regression_with_sourcemap_enabled():
    from pyteal.stack_frame import StackFrames

    originally = StackFrames._no_stackframes
    StackFrames._no_stackframes = False

    no_regressions()

    StackFrames._no_stackframes = originally


@pytest.mark.serial
def test_no_regression_with_sourcemap_disabled():
    from pyteal.stack_frame import StackFrames

    originally = StackFrames._no_stackframes

    StackFrames._no_stackframes = True

    no_regressions()

    StackFrames._no_stackframes = originally


@pytest.mark.serial
def test_sourcemap_fails_because_unconfigured():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions
    from pyteal.compiler.sourcemap import SourceMapDisabledError

    with pytest.raises(SourceMapDisabledError) as smde:
        router.compile(
            version=6,
            optimize=OptimizeOptions(scratch_slots=True),
            with_sourcemaps=True,
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

    assert compilation.approval_sourcemap

    return compilation.approval_sourcemap.annotated_teal()


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
@pytest.mark.serial
def test_time_benchmark_under_config():
    from pyteal.stack_frame import StackFrames

    print(f"{StackFrames.sourcemapping_is_off()=}")

    trial(simple_compilation)
    trial(simple_compilation)

    assert False


"""RESULTS FROM test_time_benchmark_under_config()
Frames.skipping_all()=True
simple_compilation: avg=0.013368103946639953, N=749
simple_compilation: avg=0.01360061149234357, N=736

--memray results:
======================================================================== MEMRAY REPORT ========================================================================
Allocations results for tests/unit/sourcemap_test.py::test_time_benchmark_under_config

         📦 Total memory allocated: 15.0MiB
         📏 Total allocations: 432,949
         📊 Histogram of allocation sizes: |  █ ▁    |
         🥇 Biggest allocating functions:
                - updatecache:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/linecache.py:137 -> 1.1MiB
                - updatecache:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/linecache.py:137 -> 1.0MiB
                - __init__:/Users/zeph/github/tzaffi/pyteal/pyteal/ir/tealblock.py:18 -> 1.0MiB
                - updatecache:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/linecache.py:137 -> 1.0MiB
                - _compile_bytecode:<frozen importlib._bootstrap_external>:672 -> 1.0MiB

"""


@pytest.mark.skip()
@mock.patch.object(ConfigParser, "getboolean", return_value=True)
@pytest.mark.serial
def test_time_benchmark_sourcemap_enabled(_):
    """
    UPSHOT: expect deterioration of (5 to 15)X when enabling source maps.
    """
    from pyteal.stack_frame import StackFrames

    print(f"{StackFrames.sourcemapping_is_off()=}")
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


"""RESULTS FROM test_time_benchmark_sourcemap_enabled
Frames.skipping_all()=False
>>>>>>>>>>>>>>>>>>keep_all: bool = False,<<<<<<<<<<<<<<<<<<<<<<
stop_after_first_pyteal: bool = True,
keep_one_frame_only: bool = True,
_______
simple_compilation: avg=0.10818169962975287, N=93   <---- FIRST RUN RESULT CAN PROBLY BE DISCARDED
simple_compilation: avg=0.07248607299310698, N=139
source_map_compilation: avg=0.07400739454004886, N=137
source_map_compilation: avg=0.07380111077252556, N=136
annotated_teal: avg=0.0730285696739698, N=137
annotated_teal: avg=0.07186885220663888, N=140

--memray results:
======================================================================== MEMRAY REPORT ========================================================================
Allocations results for tests/unit/sourcemap_test.py::test_time_benchmark_sourcemap_enabled

         📦 Total memory allocated: 40.2MiB
         📏 Total allocations: 2,944,972
         📊 Histogram of allocation sizes: |    █    |
         🥇 Biggest allocating functions:
                - parse:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/ast.py:50 -> 5.1MiB
                - compile_similar_to:/Users/zeph/github/tzaffi/pyteal/py310ptt/lib/python3.10/site-packages/executing/executing.py:519 -> 4.0MiB
                - format:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/traceback.py:447 -> 2.0MiB
                - __init__:/Users/zeph/github/tzaffi/pyteal/py310ptt/lib/python3.10/site-packages/executing/executing.py:236 -> 1.3MiB
                - _compile_bytecode:<frozen importlib._bootstrap_external>:672 -> 1.1MiB

_______ _______ _______ _______
Frames.skipping_all()=False
>>>>>>>>>>>>>>>>>>keep_all: bool = True,<<<<<<<<<<<<<<<<<<<<<<
stop_after_first_pyteal: bool = True,
keep_one_frame_only: bool = True,
_______
simple_compilation: avg=0.1326251971094232, N=76
simple_compilation: avg=0.0847121106476343, N=119
source_map_compilation: avg=0.07992530247521779, N=126
source_map_compilation: avg=0.08953454451901573, N=112
annotated_teal: avg=0.07898699204752764, N=127
annotated_teal: avg=0.07613436200402, N=132

--memray results:
======================================================================== MEMRAY REPORT ========================================================================
Allocations results for tests/unit/sourcemap_test.py::test_time_benchmark_sourcemap_enabled

         📦 Total memory allocated: 44.2MiB
         📏 Total allocations: 2,875,365
         📊 Histogram of allocation sizes: |  ▁ █    |
         🥇 Biggest allocating functions:
                - parse:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/ast.py:50 -> 7.0MiB
                - format:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/traceback.py:447 -> 2.0MiB
                - compile_similar_to:/Users/zeph/github/tzaffi/pyteal/py310ptt/lib/python3.10/site-packages/executing/executing.py:519 -> 2.0MiB
                - _compile_bytecode:<frozen importlib._bootstrap_external>:672 -> 1.1MiB
                - updatecache:/Users/zeph/.asdf/installs/python/3.10.4/lib/python3.10/linecache.py:137 -> 1.1MiB
"""


@pytest.mark.serial
def test_config():
    from pyteal.stack_frame import StackFrames

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

    assert ["enabled", "debug"] == config.options("pyteal-source-mapper")

    assert config.getboolean("pyteal-source-mapper", "enabled") is False
    assert StackFrames.sourcemapping_is_off() is True

    StackFrames._no_stackframes = False
    assert StackFrames.sourcemapping_is_off() is False
    assert StackFrames.sourcemapping_is_off(_force_refresh=True) is True


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
    assert len(approval1.splitlines()) == len(
        approval2.splitlines()
    ), "TODO: this is probly because of a temporary change to the router"
    assert approval1 == approval2
