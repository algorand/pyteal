from pathlib import Path

from pyteal.compiler import compileTeal
from pyteal.ir import Mode

PATH = Path.cwd() / "tests" / "unit"
FIXTURES = PATH / "teal"
GENERATED = PATH / "generated"


def compile_and_save(approval, version, test_name):
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


def mismatch_ligature(expected, actual):
    la, le = len(actual), len(expected)
    mm_idx = -1
    for i in range(min(la, le)):
        if expected[i] != actual[i]:
            mm_idx = i
            break
    if mm_idx < 0:
        return ""
    return " " * (mm_idx) + "X" + "-" * (max(la, le) - mm_idx - 1)


def assert_teal_as_expected(path2actual, path2expected):
    with open(path2actual, "r") as fa, open(path2expected, "r") as fe:
        alines = fa.read().split("\n")
        elines = fe.read().split("\n")

        assert len(elines) == len(
            alines
        ), f"""EXPECTED {len(elines)} lines for {path2expected} but ACTUALLY got {len(alines)} lines in {path2actual}"""

        for i, actual in enumerate(alines):
            expected = elines[i]
            assert expected.startswith(
                actual
            ), f"""ACTUAL line in {path2actual}
LINE{i+1}:
{actual}
{mismatch_ligature(expected, actual)}
DOES NOT prefix the EXPECTED (which should have been actual + some commentary) in {path2expected}:
LINE{i+1}:
{expected}  
{mismatch_ligature(expected, actual)}
"""


def assert_new_v_old(approve_func, version, test_name):
    tealdir, name, compiled = compile_and_save(approve_func, version, test_name)

    print(
        f"""Compilation resulted in TEAL program of length {len(compiled)}. 
To view output SEE <{name}.teal> in ({tealdir})
--------------"""
    )

    path2actual = tealdir / (name + ".teal")
    path2expected = FIXTURES / test_name / (name + ".teal")
    assert_teal_as_expected(path2actual, path2expected)
