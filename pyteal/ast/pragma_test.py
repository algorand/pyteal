import pytest
import pkg_resources

import pyteal as pt
from pyteal.ast.pragma import __convert_pep440_compiler_version


@pytest.fixture
def mock_version(version: str, monkeypatch: pytest.MonkeyPatch):
    def mocked_require(name: str):
        if (
            name == "pyteal"
            and version is not None  # don't mock if no version is specified
        ):
            return [
                pkg_resources.Distribution(
                    version=version,
                )
            ]
        else:
            return pkg_resources.require(name)[0]

    monkeypatch.setattr(pkg_resources, "require", mocked_require)


@pytest.mark.parametrize(
    "compiler_version,expected",
    [
        ("2", "2.0.0"),
        (">=0.12.0a9.post2.dev9", ">=0.12.0-alpha9.2.9"),
        ("<0.5.0 || >=1.0.0a9.post1.dev2", "<0.5.0 || >=1.0.0-alpha9.1.2"),
        ("v0.12.9.post1 - v1.13.0.dev1", "0.12.9-1.0 - 1.13.0-0.1"),
        (
            "1.2.3a4.post5.dev6+AVM7.1",
            "1.2.3-alpha4.5.6+avm7.1",
        ),  # local versions are lowercased to be consistent with pkg_resources
    ],
)
def test_convert_pep440_compiler_version(compiler_version, expected):
    assert __convert_pep440_compiler_version(compiler_version) == expected


@pytest.mark.usefixtures("mock_version")
@pytest.mark.parametrize(
    "version, compiler_version, should_error",
    [
        # valid
        ("0.12.0", "0.12.0", False),
        ("0.12.0", "<=0.12.0", False),
        ("0.12.0", ">=0.12.0", False),
        ("0.13.0", "<0.8.0 || >=0.12.0", False),
        ("0.12.0", "0.12.0-rc1", False),
        ("0.1.0", "<0.2.0", False),
        ("0.1.0a1", "<0.1.0a2", False),
        ("0.1.0-rc1", "<0.1.0-rc2", False),
        ("0.1.0.dev1", "<0.1.0.dev2", False),
        ("0.1.0a9.dev2", ">0.1.0a8.dev1", False),
        ("v1.1", "<0.5.0 || >=1.0.0a9.post1.dev2", False),
        ("v1.0a9.post2.dev2", "<0.5.0 || >=1.0.0a9.post1.dev2", False),
        ("v1.0a9.post1", "<0.5.0 || >=1.0.0a9.dev10", False),
        ("0.4.0", "<0.5.0 || >=1.0.0a9.dev10", False),
        ("1.2.3a4.post5.dev6+AVM7.1", "=1.2.3a4.post5.dev6+AVM7.1", False),
        (
            "1.0.0+AVM7.1",
            "=1.0.0",
            False,
        ),  # Ignores local version (consistent with PEP 440)
        (
            pkg_resources.require("pyteal")[0].version,
            pkg_resources.require("pyteal")[0].version,
            False,
        ),
        # invalid
        ("0.13.0", "0.13.1", True),
        ("1.2.3a2", "<0.8.0 || >=0.12.0", True),
        ("0.1.0a1", "<0.2.0", True),
        ("0.4.0b10", "<0.5.0 || >=1.0.0a9.dev10", True),
        ("0.4.9a10.dev2.post3", "<0.5.0 || >=1.0.0a9.post1.dev2", True),
    ],
)
def test_pragma_compiler_version(version, compiler_version, should_error):
    if should_error:
        with pytest.raises(pt.TealPragmaError):
            pt.pragma(compiler_version=compiler_version)
    else:
        pt.pragma(compiler_version=compiler_version)


@pytest.mark.parametrize(
    "compiler_version",
    ["not a version", ">=0.1.1,<0.3.0", "1.2.3aq"],  # incorrect spec  # invalid PEP 440
)
def test_pragma_compiler_version_invalid(compiler_version):
    with pytest.raises(ValueError):
        pt.pragma(compiler_version=compiler_version)


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
