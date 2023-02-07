import pytest

import pyteal as pt
from pyteal.ast.seq import _use_seq_if_multiple

options = pt.CompileOptions()


def test_seq_zero():
    for expr in (pt.Seq(), pt.Seq([])):
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected = pt.TealSimpleBlock([])

        actual, _ = expr.__teal__(options)

        assert actual == expected


def test_seq_one():
    items = [pt.Int(0)]
    expr = pt.Seq(items)
    assert expr.type_of() == pt.TealType.uint64

    expected, _ = items[0].__teal__(options)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_seq_two():
    items = [pt.App.localPut(pt.Int(0), pt.Bytes("key"), pt.Int(1)), pt.Int(7)]
    expr = pt.Seq(items)
    assert expr.type_of() == items[-1].type_of()

    expected, first_end = items[0].__teal__(options)
    first_end.setNextBlock(items[1].__teal__(options)[0])
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_seq_three():
    items = [
        pt.App.localPut(pt.Int(0), pt.Bytes("key1"), pt.Int(1)),
        pt.App.localPut(pt.Int(1), pt.Bytes("key2"), pt.Bytes("value2")),
        pt.Pop(pt.Bytes("end")),
    ]
    expr = pt.Seq(items)
    assert expr.type_of() == items[-1].type_of()

    expected, first_end = items[0].__teal__(options)
    second_start, second_end = items[1].__teal__(options)
    first_end.setNextBlock(second_start)
    third_start, _ = items[2].__teal__(options)
    second_end.setNextBlock(third_start)

    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_seq_has_return():
    exprWithReturn = pt.Seq(
        [
            pt.App.localPut(pt.Int(0), pt.Bytes("key1"), pt.Int(1)),
            pt.Return(pt.Int(1)),
        ]
    )
    assert exprWithReturn.has_return()

    exprWithoutReturn = pt.Seq(
        [pt.App.localPut(pt.Int(0), pt.Bytes("key1"), pt.Int(1)), pt.Int(1)]
    )
    assert not exprWithoutReturn.has_return()


def test_seq_invalid():
    with pytest.raises(pt.TealSeqError):
        pt.Seq([pt.Int(1), pt.Pop(pt.Int(2))])

    with pytest.raises(pt.TealSeqError):
        pt.Seq([pt.Int(1), pt.Int(2)])

    with pytest.raises(pt.TealSeqError):
        pt.Seq([pt.Seq([pt.Pop(pt.Int(1)), pt.Int(2)]), pt.Int(3)])


def test_seq_overloads_equivalence():
    items = [
        pt.App.localPut(pt.Int(0), pt.Bytes("key1"), pt.Int(1)),
        pt.App.localPut(pt.Int(1), pt.Bytes("key2"), pt.Bytes("value2")),
        pt.Pop(pt.Bytes("end")),
    ]
    expr1 = pt.Seq(items)
    expr2 = pt.Seq(*items)

    expected = expr1.__teal__(options)
    actual = expr2.__teal__(options)

    assert actual == expected


def test_use_seq_if_multiple():
    # Test a single expression
    items = [pt.Int(1)]
    expr = _use_seq_if_multiple(*items)

    expected = items[0].__teal__(options)
    actual = expr.__teal__(options)

    assert actual == expected

    # Test multiple expressions
    items = [pt.Pop(pt.Int(1)), pt.Int(2)]
    expr = _use_seq_if_multiple(*items)

    expected = pt.Seq(items).__teal__(options)
    actual = expr.__teal__(options)

    assert actual == expected


def test_use_seq_if_multiple_overloads_equivalence():
    items = [pt.Pop(pt.Int(1)), pt.Int(2)]
    expr = _use_seq_if_multiple(items)

    expected = pt.Seq(items).__teal__(options)
    actual = expr.__teal__(options)

    assert actual == expected
