import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_and_one():
    arg = pt.Int(1)
    expr = pt.And(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(arg, pt.Op.int, 1)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_and_two():
    args = [pt.Int(1), pt.Int(2)]
    expr = pt.And(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.logic_and),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_and_three():
    args = [pt.Int(1), pt.Int(2), pt.Int(3)]
    expr = pt.And(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.logic_and),
            pt.TealOp(args[2], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.logic_and),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_and_overload():
    args = [pt.Int(1), pt.Int(2)]
    expr = args[0].And(args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.logic_and),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_and_invalid():
    with pytest.raises(pt.TealInputError):
        pt.And()

    with pytest.raises(pt.TealTypeError):
        pt.And(pt.Int(1), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.And(pt.Txn.receiver(), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.And(pt.Txn.receiver(), pt.Txn.receiver())


def test_or_one():
    arg = pt.Int(1)
    expr = pt.Or(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(arg, pt.Op.int, 1)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_or_two():
    args = [pt.Int(1), pt.Int(0)]
    expr = pt.Or(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.logic_or),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_or_three():
    args = [pt.Int(0), pt.Int(1), pt.Int(2)]
    expr = pt.Or(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 0),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.logic_or),
            pt.TealOp(args[2], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.logic_or),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_or_overload():
    args = [pt.Int(1), pt.Int(0)]
    expr = args[0].Or(args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.logic_or),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_or_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Or()

    with pytest.raises(pt.TealTypeError):
        pt.Or(pt.Int(1), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Or(pt.Txn.receiver(), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.Or(pt.Txn.receiver(), pt.Txn.receiver())


def test_concat_one():
    arg = pt.Bytes("a")
    expr = pt.Concat(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock([pt.TealOp(arg, pt.Op.byte, '"a"')])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_concat_two():
    args = [pt.Bytes("a"), pt.Bytes("b")]
    expr = pt.Concat(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"a"'),
            pt.TealOp(args[1], pt.Op.byte, '"b"'),
            pt.TealOp(expr, pt.Op.concat),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_concat_three():
    args = [pt.Bytes("a"), pt.Bytes("b"), pt.Bytes("c")]
    expr = pt.Concat(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"a"'),
            pt.TealOp(args[1], pt.Op.byte, '"b"'),
            pt.TealOp(expr, pt.Op.concat),
            pt.TealOp(args[2], pt.Op.byte, '"c"'),
            pt.TealOp(expr, pt.Op.concat),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_concat_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Concat()

    with pytest.raises(pt.TealTypeError):
        pt.Concat(pt.Int(1), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Concat(pt.Txn.receiver(), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.Concat(pt.Int(1), pt.Int(2))
