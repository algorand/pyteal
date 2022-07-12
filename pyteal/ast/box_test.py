from typing import Tuple

import pytest
import pyteal as pt

teal6Options = pt.CompileOptions(version=6)
teal7Options = pt.CompileOptions(version=7)


def test_compile_version_and_type():
    TEST_CASES: list[Tuple[pt.Expr, pt.TealType]] = [
        (pt.Box.create(pt.Bytes("box"), pt.Int(10)), pt.TealType.none),
        (pt.Box.delete(pt.Bytes("box")), pt.TealType.none),
        (pt.Box.extract(pt.Bytes("box"), pt.Int(2), pt.Int(4)), pt.TealType.bytes),
        (
            pt.Box.replace(pt.Bytes("box"), pt.Int(3), pt.Bytes("replace")),
            pt.TealType.none,
        ),
        (pt.Box.length(pt.Bytes("box")), pt.TealType.none),
        (pt.Box.get(pt.Bytes("box")), pt.TealType.none),
        (pt.Box.put(pt.Bytes("box"), pt.Bytes("goonery")), pt.TealType.none),
    ]

    for test_case, test_case_type in TEST_CASES:
        with pytest.raises(pt.TealInputError):
            test_case.__teal__(teal6Options)

        test_case.__teal__(teal7Options)

        assert test_case.type_of() == test_case_type
        assert not test_case.has_return()
