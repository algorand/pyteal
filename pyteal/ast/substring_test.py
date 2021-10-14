import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions(version=2)
teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)


def test_substring_immediate_v2():
    args = [Bytes("my string"), Int(0), Int(2)]
    expr = Substring(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"my string"'),
            TealOp(expr, Op.substring, 0, 2),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_substring_immediate_v5():
    args = [Bytes("my string"), Int(1), Int(2)]
    expr = Substring(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"my string"'),
            TealOp(expr, Op.extract, 1, 1),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_substring_to_extract():
    my_string = "a" * 257
    args = [Bytes(my_string), Int(255), Int(257)]
    expr = Substring(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"{my_string}"'.format(my_string=my_string)),
            TealOp(expr, Op.extract, 255, 2),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_substring_stack_v2():
    my_string = "a" * 257
    args = [Bytes(my_string), Int(256), Int(257)]
    expr = Substring(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"{my_string}"'.format(my_string=my_string)),
            TealOp(args[1], Op.int, 256),
            TealOp(args[2], Op.int, 257),
            TealOp(expr, Op.substring3),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_substring_stack_v5():
    my_string = "a" * 257
    args = [Bytes(my_string), Int(256), Int(257)]
    expr = Substring(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"{my_string}"'.format(my_string=my_string)),
            TealOp(args[1], Op.int, 256),
            TealOp(Int(1), Op.int, 1),
            TealOp(expr, Op.extract3),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_zero_length_substring_immediate():
    my_string = "a" * 257
    args = [Bytes(my_string), Int(1), Int(1)]
    expr = Substring(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"{my_string}"'.format(my_string=my_string)),
            TealOp(expr, Op.substring, 1, 1),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_substring_invalid():
    with pytest.raises(TealTypeError):
        Substring(Int(0), Int(0), Int(2))

    with pytest.raises(TealTypeError):
        Substring(Bytes("my string"), Txn.sender(), Int(2))

    with pytest.raises(TealTypeError):
        Substring(Bytes("my string"), Int(0), Txn.sender())

    with pytest.raises(Exception):
        Substring(Bytes("my string"), Int(1), Int(0)).__teal__(teal5Options)


def test_extract_immediate():
    args = [Bytes("my string"), Int(0), Int(2)]
    expr = Extract(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"my string"'),
            TealOp(expr, Op.extract, 0, 2),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_extract_zero():
    args = [Bytes("my string"), Int(1), Int(0)]
    expr = Extract(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"my string"'),
            TealOp(args[1], Op.int, 1),
            TealOp(args[2], Op.int, 0),
            TealOp(expr, Op.extract3),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_extract_stack():
    my_string = "*" * 257
    args = [Bytes(my_string), Int(256), Int(257)]
    expr = Extract(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"{my_string}"'.format(my_string=my_string)),
            TealOp(args[1], Op.int, 256),
            TealOp(args[2], Op.int, 257),
            TealOp(expr, Op.extract3),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_extract_invalid():
    with pytest.raises(TealTypeError):
        Extract(Int(0), Int(0), Int(2))

    with pytest.raises(TealTypeError):
        Extract(Bytes("my string"), Txn.sender(), Int(2))

    with pytest.raises(TealTypeError):
        Extract(Bytes("my string"), Int(0), Txn.sender())


def test_suffix_immediate():
    args = [Bytes("my string"), Int(1)]
    expr = Suffix(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"my string"'),
            TealOp(expr, Op.extract, 1, 0),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_suffix_stack():
    my_string = "*" * 1024
    args = [Bytes(my_string), Int(257)]
    expr = Suffix(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"{my_string}"'.format(my_string=my_string)),
            TealOp(args[1], Op.int, 257),
            TealOp(expr, Op.dig, 1),
            TealOp(expr, Op.len),
            TealOp(expr, Op.substring3),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_suffix_invalid():
    with pytest.raises(TealTypeError):
        Suffix(Int(0), Int(0))

    with pytest.raises(TealTypeError):
        Suffix(Bytes("my string"), Txn.sender())
