from pathlib import Path
from difflib import unified_diff

from pyteal.compiler import compileTeal
from pyteal.ir import Mode

PATH = Path.cwd() / "tests" / "unit"
FIXTURES = PATH / "teal"
GENERATED = PATH / "generated"


def compile_and_save(approval, version: int, test_name: str) -> tuple[Path, str, str]:
    compiled = compileTeal(approval(), mode=Mode.Application, version=version)
    name = approval.__name__
    tealdir = GENERATED / test_name
    tealdir.mkdir(parents=True, exist_ok=True)
    with open(tealdir / (name + ".teal"), "w") as f:
        f.write(compiled)
    print(
        f"""Successfuly tested approval program <<{name}>> having 
compiled it into {len(compiled)} characters. See the results in:
{tealdir}
"""
    )
    return tealdir, name, compiled


def process_line(line: str) -> str:
    quote_types = ("'", '"')
    comment_start = "/"

    processed_end = len(line) - 1

    current_quote: str | None = None
    for i, char in enumerate(line):
        for qt in quote_types:
            if char == qt:
                if current_quote == qt:
                    # breaking out of quote
                    current_quote = None
                elif current_quote is None:
                    current_quote = qt
                    # entering a quote
        if current_quote is None:
            # not in a quote
            if (
                char == comment_start
                and i + 1 < len(line)
                and line[i + 1] == comment_start
            ):
                # a comment is about to start, ignore rest of line
                processed_end = i - 1
                break

    return line[:processed_end].strip() + "\n"


def assert_teal_as_expected(path2actual: Path, path2expected: Path):
    with open(path2actual, "r") as fa, open(path2expected, "r") as fe:
        actual_lines = [process_line(l) for l in fa.readlines()]
        expected_lines = [process_line(l) for l in fe.readlines()]

    diff = list(
        unified_diff(
            expected_lines,
            actual_lines,
            fromfile=str(path2expected),
            tofile=str(path2actual),
            n=3,
        )
    )

    assert (
        len(diff) == 0
    ), f"Difference between expected and actual TEAL code:\n\n{''.join(diff)}"


def assert_new_v_old(approve_func, version: int, test_name: str):
    tealdir, name, compiled = compile_and_save(approve_func, version, test_name)

    print(
        f"""Compilation resulted in TEAL program of length {len(compiled)}. 
To view output SEE <{name}.teal> in ({tealdir})
--------------"""
    )

    path2actual = tealdir / (name + ".teal")
    path2expected = FIXTURES / test_name / (name + ".teal")
    assert_teal_as_expected(path2actual, path2expected)
