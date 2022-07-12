import pytest
import pyteal as pt

teal6Options = pt.CompileOptions(version=6)
teal7Options = pt.CompileOptions(version=7)


def test_compile_version_correct():
    TEST_CASES: list[pt.Expr] = [
        pt.Box.create(pt.Bytes("box"), pt.Int(10)),
        pt.Box.delete(pt.Bytes("box")),
        pt.Box.extract(pt.Bytes("box"), pt.Int(2), pt.Int(4)),
        pt.Box.replace(pt.Bytes("box"), pt.Int(3), pt.Bytes("replace")),
        pt.Box.length(pt.Bytes("box")),
        pt.Box.get(pt.Bytes("box")),
        pt.Box.put(pt.Bytes("box"), pt.Bytes("goonery")),
    ]

    for test_case in TEST_CASES:
        with pytest.raises(pt.TealInputError):
            test_case.__teal__(teal6Options)

        test_case.__teal__(teal7Options)
