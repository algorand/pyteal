from typing import Callable, Tuple

import pytest
import pyteal as pt

avm7Options = pt.CompileOptions(version=7)
avm8Options = pt.CompileOptions(version=8)

POSITIVE_TEST_CASES: list[Tuple[pt.Expr, pt.TealType]] = [
    (pt.BoxCreate(pt.Bytes("box"), pt.Int(10)), pt.TealType.uint64),
    (pt.BoxDelete(pt.Bytes("box")), pt.TealType.uint64),
    (pt.BoxExtract(pt.Bytes("box"), pt.Int(2), pt.Int(4)), pt.TealType.bytes),
    (
        pt.BoxReplace(pt.Bytes("box"), pt.Int(3), pt.Bytes("replace")),
        pt.TealType.none,
    ),
    (pt.BoxLen(pt.Bytes("box")), pt.TealType.none),
    (pt.BoxGet(pt.Bytes("box")), pt.TealType.none),
    (pt.BoxPut(pt.Bytes("box"), pt.Bytes("goonery")), pt.TealType.none),
]


@pytest.mark.parametrize("test_case, test_case_type", POSITIVE_TEST_CASES)
def test_compile_version_and_type(test_case, test_case_type):
    with pytest.raises(pt.TealInputError):
        test_case.__teal__(avm7Options)

    test_case.__teal__(avm8Options)
    assert test_case.type_of() == test_case_type
    assert not test_case.has_return()

    return


INVALID_TEST_CASES: list[Tuple[list[pt.Expr], type | Callable[..., pt.MaybeValue]]] = [
    ([pt.Bytes("box"), pt.Bytes("ten")], pt.BoxCreate),
    ([pt.Int(0xB0B), pt.Int(10)], pt.BoxCreate),
    ([pt.Int(0xA11CE)], pt.BoxDelete),
    ([pt.Bytes("box"), pt.Int(2), pt.Bytes("three")], pt.BoxExtract),
    ([pt.Bytes("box"), pt.Int(2), pt.Int(0x570FF)], pt.BoxReplace),
    ([pt.Int(12)], pt.BoxLen),
    ([pt.Int(45)], pt.BoxGet),
    ([pt.Bytes("box"), pt.Int(123)], pt.BoxPut),
]


@pytest.mark.parametrize("test_args, test_expr", INVALID_TEST_CASES)
def test_box_invalid_args(test_args, test_expr):
    with pytest.raises(pt.TealTypeError):
        test_expr(*test_args)


def test_box_create_compile():
    name_arg: pt.Expr = pt.Bytes("eineName")
    size_arg: pt.Expr = pt.Int(10)
    expr: pt.Expr = pt.BoxCreate(name_arg, size_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(size_arg, pt.Op.int, 10),
            pt.TealOp(expr, pt.Op.box_create),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual


def test_box_delete_compile():
    name_arg: pt.Expr = pt.Bytes("eineName")
    expr: pt.Expr = pt.BoxDelete(name_arg)

    expected = pt.TealSimpleBlock(
        [pt.TealOp(name_arg, pt.Op.byte, '"eineName"'), pt.TealOp(expr, pt.Op.box_del)]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual


def test_box_extract():
    name_arg: pt.Expr = pt.Bytes("eineName")
    srt_arg: pt.Expr = pt.Int(10)
    end_arg: pt.Expr = pt.Int(15)
    expr: pt.Expr = pt.BoxExtract(name_arg, srt_arg, end_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(srt_arg, pt.Op.int, 10),
            pt.TealOp(end_arg, pt.Op.int, 15),
            pt.TealOp(expr, pt.Op.box_extract),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual


def test_box_replace():
    name_arg: pt.Expr = pt.Bytes("eineName")
    srt_arg: pt.Expr = pt.Int(10)
    replace_arg: pt.Expr = pt.Bytes("replace-str")
    expr: pt.Expr = pt.BoxReplace(name_arg, srt_arg, replace_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(srt_arg, pt.Op.int, 10),
            pt.TealOp(replace_arg, pt.Op.byte, '"replace-str"'),
            pt.TealOp(expr, pt.Op.box_replace),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual


def test_box_length():
    name_arg: pt.Expr = pt.Bytes("eineName")
    expr: pt.MaybeValue = pt.BoxLen(name_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, '"eineName"'),
            pt.TealOp(None, pt.Op.box_len),
            pt.TealOp(None, pt.Op.store, expr.output_slots[1]),
            pt.TealOp(None, pt.Op.store, expr.output_slots[0]),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert expected == actual


def test_box_get():
    name_arg: pt.Expr = pt.Bytes("eineName")
    expr: pt.MaybeValue = pt.BoxGet(name_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, '"eineName"'),
            pt.TealOp(None, pt.Op.box_get),
            pt.TealOp(None, pt.Op.store, expr.output_slots[1]),
            pt.TealOp(None, pt.Op.store, expr.output_slots[0]),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert expected == actual


def test_box_put():
    name_arg: pt.Expr = pt.Bytes("eineName")
    put_arg: pt.Expr = pt.Bytes("put-str")
    expr: pt.Expr = pt.BoxPut(name_arg, put_arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(name_arg, pt.Op.byte, '"eineName"'),
            pt.TealOp(put_arg, pt.Op.byte, '"put-str"'),
            pt.TealOp(expr, pt.Op.box_put),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert expected == actual
