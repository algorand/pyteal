import pytest

import pyteal as pt

avm6Options = pt.CompileOptions(version=6)
avm7Options = pt.CompileOptions(version=7)


def test_replace_immediate():
    args = [pt.Bytes("my string"), pt.Int(0), pt.Bytes("abcdefghi")]
    expr = pt.Replace(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"my string"'),
            pt.TealOp(args[2], pt.Op.byte, '"abcdefghi"'),
            pt.TealOp(expr, pt.Op.replace2, 0),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_replace_stack_int():
    my_string = "*" * 257
    args = [pt.Bytes(my_string), pt.Int(256), pt.Bytes("ab")]
    expr = pt.Replace(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(args[1], pt.Op.int, 256),
            pt.TealOp(args[2], pt.Op.byte, '"ab"'),
            pt.TealOp(expr, pt.Op.replace3),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


# Mirrors `test_replace_stack_int`, but attempts replacement with start != pt.Int.
def test_replace_stack_not_int():
    my_string = "*" * 257
    add = pt.Add(pt.Int(254), pt.Int(2))
    args = [pt.Bytes(my_string), add, pt.Bytes("ab")]
    expr = pt.Replace(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(pt.Int(254), pt.Op.int, 254),
            pt.TealOp(pt.Int(2), pt.Op.int, 2),
            pt.TealOp(add, pt.Op.add),
            pt.TealOp(args[2], pt.Op.byte, '"ab"'),
            pt.TealOp(expr, pt.Op.replace3),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_replace_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Replace(pt.Bytes("my string"), pt.Int(0), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.Replace(
            pt.Bytes("my string"), pt.Bytes("should be int"), pt.Bytes("abcdefghi")
        )

    with pytest.raises(pt.TealTypeError):
        pt.Replace(pt.Bytes("my string"), pt.Txn.sender(), pt.Bytes("abcdefghi"))
