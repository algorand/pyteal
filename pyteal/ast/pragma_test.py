import pytest
from tests.mock_version import mock_version  # noqa: F401

import pyteal as pt


@pytest.mark.usefixtures("mock_version")
@pytest.mark.parametrize(
    "version, compiler_version, should_error",
    [
        # valid
        ("0.12.0", "0.12.0", False),
        (
            "1.0.0+AVM7.1",
            "=1.0.0",
            False,
        ),
        # invalid
        ("0.13.0", "0.13.1", True),
        ("1.2.3a2", "<0.8.0 || >=0.12.0", True),
    ],
)
def test_pragma_expr(compiler_version, should_error):
    program = pt.Pragma(pt.Approve(), compiler_version=compiler_version)

    if should_error:
        with pytest.raises(pt.TealPragmaError):
            pt.compileTeal(program, mode=pt.Mode.Application, version=6)
    else:
        pt.compileTeal(program, mode=pt.Mode.Application, version=6)


def test_pragma_expr_does_not_change():
    without_pragma = pt.Seq(pt.Pop(pt.Add(pt.Int(1), pt.Int(2))), pt.Return(pt.Int(1)))
    pragma = pt.Pragma(without_pragma, compiler_version=">=0.0.0")

    compiled_with_pragma = pt.compileTeal(pragma, mode=pt.Mode.Application, version=6)
    compiled_without_pragma = pt.compileTeal(
        without_pragma, mode=pt.Mode.Application, version=6
    )

    assert compiled_with_pragma == compiled_without_pragma


def test_pragma_expr_has_return():
    exprWithReturn = pt.Pragma(pt.Return(pt.Int(1)), compiler_version=">=0.0.0")
    assert exprWithReturn.has_return()

    exprWithoutReturn = pt.Pragma(pt.Int(1), compiler_version=">=0.0.0")
    assert not exprWithoutReturn.has_return()


@pytest.mark.parametrize(
    "compiler_version",
    ["not a version", ">=0.1.1,<0.3.0", "1.2.3aq"],  # incorrect spec  # invalid PEP 440
)
def test_pragma_expr_invalid_compiler_version(compiler_version):
    with pytest.raises(ValueError):
        pt.Pragma(pt.Approve(), compiler_version=compiler_version)
