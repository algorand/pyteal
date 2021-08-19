import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_and_two():
    args = [Int(1), Int(2)]
    expr = And(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 2),
            TealOp(expr, Op.logic_and),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_and_three():
    args = [Int(1), Int(2), Int(3)]
    expr = And(args[0], args[1], args[2])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 2),
            TealOp(expr, Op.logic_and),
            TealOp(args[2], Op.int, 3),
            TealOp(expr, Op.logic_and),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_and_overload():
    args = [Int(1), Int(2)]
    expr = args[0].And(args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 2),
            TealOp(expr, Op.logic_and),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_and_invalid():
    with pytest.raises(TealInputError):
        And()

    with pytest.raises(TealInputError):
        And(Int(1))

    with pytest.raises(TealTypeError):
        And(Int(1), Txn.receiver())

    with pytest.raises(TealTypeError):
        And(Txn.receiver(), Int(1))

    with pytest.raises(TealTypeError):
        And(Txn.receiver(), Txn.receiver())


def test_or_two():
    args = [Int(1), Int(0)]
    expr = Or(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 0),
            TealOp(expr, Op.logic_or),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_or_three():
    args = [Int(0), Int(1), Int(2)]
    expr = Or(args[0], args[1], args[2])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 0),
            TealOp(args[1], Op.int, 1),
            TealOp(expr, Op.logic_or),
            TealOp(args[2], Op.int, 2),
            TealOp(expr, Op.logic_or),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_or_overload():
    args = [Int(1), Int(0)]
    expr = args[0].Or(args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 0),
            TealOp(expr, Op.logic_or),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_or_invalid():
    with pytest.raises(TealInputError):
        Or()

    with pytest.raises(TealInputError):
        Or(Int(1))

    with pytest.raises(TealTypeError):
        Or(Int(1), Txn.receiver())

    with pytest.raises(TealTypeError):
        Or(Txn.receiver(), Int(1))

    with pytest.raises(TealTypeError):
        Or(Txn.receiver(), Txn.receiver())
