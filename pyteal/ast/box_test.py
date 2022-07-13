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
    name_arg: pt.Expr = pt.Bytes("eineName")
    size_arg: pt.Expr = pt.Int(10)
    expr: pt.Expr = pt.Box.create(name_arg, size_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(size_arg, pt.Op.int, 10),
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(expr, pt.Op.box_create),
        ]
    )
    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual


def test_box_delete_compile():
    name_arg: pt.Expr = pt.Bytes("eineName")
    expr: pt.Expr = pt.Box.delete(name_arg)

    expected = pt.TealSimpleBlock(
        [pt.TealOp(name_arg, pt.Op.byte, '"eineName"'), pt.TealOp(expr, pt.Op.box_del)]
    )
    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual


def test_box_extract():
    name_arg: pt.Expr = pt.Bytes("eineName")
    srt_arg: pt.Expr = pt.Int(10)
    end_arg: pt.Expr = pt.Int(15)
    expr: pt.Expr = pt.Box.extract(name_arg, srt_arg, end_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(srt_arg, pt.Op.int, 10),
            pt.TealOp(end_arg, pt.Op.int, 15),
            pt.TealOp(expr, pt.Op.box_extract),
        ]
    )
    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual


def test_box_replace():
    name_arg: pt.Expr = pt.Bytes("eineName")
    srt_arg: pt.Expr = pt.Int(10)
    replace_arg: pt.Expr = pt.Bytes("replace-str")
    expr: pt.Expr = pt.Box.replace(name_arg, srt_arg, replace_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(srt_arg, pt.Op.int, 10),
            pt.TealOp(replace_arg, pt.Op.byte, '"replace-str"'),
            pt.TealOp(expr, pt.Op.box_replace),
        ]
    )
    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual


def test_box_length():
    name_arg: pt.Expr = pt.Bytes("eineName")
    expr: pt.MultiValue = pt.Box.length(name_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(expr, pt.Op.box_len),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )
    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert expected == actual


def test_box_get():
    name_arg: pt.Expr = pt.Bytes("eineName")
    expr: pt.MultiValue = pt.Box.get(name_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(expr, pt.Op.box_get),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )
    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert expected == actual


def test_box_put():
    name_arg: pt.Expr = pt.Bytes("eineName")
    put_arg: pt.Expr = pt.Bytes("put-str")
    expr: pt.Expr = pt.Box.put(name_arg, put_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(put_arg, pt.Op.byte, '"put-str"'),
            pt.TealOp(expr, pt.Op.box_put),
        ]
    )
    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual
