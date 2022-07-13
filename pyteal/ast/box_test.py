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

    return


def test_box_invalid_args():
    with pytest.raises(pt.TealTypeError):
        pt.Box.create(pt.Bytes("box"), pt.Bytes("ten"))

    with pytest.raises(pt.TealTypeError):
        pt.Box.create(pt.Int(0xB06), pt.Int(10))

    with pytest.raises(pt.TealTypeError):
        pt.Box.delete(pt.Int(0xB06))

    with pytest.raises(pt.TealTypeError):
        pt.Box.extract(pt.Bytes("box"), pt.Int(2), pt.Bytes("three"))

    with pytest.raises(pt.TealTypeError):
        pt.Box.replace(pt.Bytes("box"), pt.Int(2), pt.Int(0x570FF))

    with pytest.raises(pt.TealTypeError):
        pt.Box.length(pt.Int(12))

    with pytest.raises(pt.TealTypeError):
        pt.Box.get(pt.Int(45))

    with pytest.raises(pt.TealTypeError):
        pt.Box.put(pt.Bytes("box"), pt.Int(123))

    return


def test_box_create_compile():
    pass


def test_box_delete_compile():
    pass


def test_box_extract():
    pass


def test_box_replace():
    pass


def test_box_length():
    pass


def test_box_get():
    pass


def test_box_put():
    pass
