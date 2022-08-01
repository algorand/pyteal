import pytest

import pyteal as pt

avm2Options = pt.CompileOptions(version=2)
avm3Options = pt.CompileOptions(version=3)
avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)


def test_substring_immediate_v2():
    args = [pt.Bytes("my string"), pt.Int(0), pt.Int(2)]
    expr = pt.Substring(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"my string"'),
            pt.TealOp(expr, pt.Op.substring, 0, 2),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_substring_immediate_v5():
    args = [pt.Bytes("my string"), pt.Int(1), pt.Int(2)]
    expr = pt.Substring(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"my string"'),
            pt.TealOp(expr, pt.Op.extract, 1, 1),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_substring_to_extract():
    my_string = "a" * 257
    args = [pt.Bytes(my_string), pt.Int(255), pt.Int(257)]
    expr = pt.Substring(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(expr, pt.Op.extract, 255, 2),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_substring_stack_v2():
    my_string = "a" * 257
    args = [pt.Bytes(my_string), pt.Int(256), pt.Int(257)]
    expr = pt.Substring(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(args[1], pt.Op.int, 256),
            pt.TealOp(args[2], pt.Op.int, 257),
            pt.TealOp(expr, pt.Op.substring3),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_substring_stack_v5():
    my_string = "a" * 257
    args = [pt.Bytes(my_string), pt.Int(256), pt.Int(257)]
    expr = pt.Substring(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(args[1], pt.Op.int, 256),
            pt.TealOp(pt.Int(1), pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.extract3),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_zero_length_substring_immediate():
    my_string = "a" * 257
    args = [pt.Bytes(my_string), pt.Int(1), pt.Int(1)]
    expr = pt.Substring(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(expr, pt.Op.substring, 1, 1),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_substring_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Substring(pt.Int(0), pt.Int(0), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.Substring(pt.Bytes("my string"), pt.Txn.sender(), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.Substring(pt.Bytes("my string"), pt.Int(0), pt.Txn.sender())

    with pytest.raises(Exception):
        pt.Substring(pt.Bytes("my string"), pt.Int(1), pt.Int(0)).__teal__(avm5Options)


def test_extract_immediate():
    args = [pt.Bytes("my string"), pt.Int(0), pt.Int(2)]
    expr = pt.Extract(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"my string"'),
            pt.TealOp(expr, pt.Op.extract, 0, 2),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm4Options)


def test_extract_zero():
    args = [pt.Bytes("my string"), pt.Int(1), pt.Int(0)]
    expr = pt.Extract(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"my string"'),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(args[2], pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.extract3),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm4Options)


def test_extract_stack():
    my_string = "*" * 257
    args = [pt.Bytes(my_string), pt.Int(256), pt.Int(257)]
    expr = pt.Extract(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(args[1], pt.Op.int, 256),
            pt.TealOp(args[2], pt.Op.int, 257),
            pt.TealOp(expr, pt.Op.extract3),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm4Options)


def test_extract_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Extract(pt.Int(0), pt.Int(0), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.Extract(pt.Bytes("my string"), pt.Txn.sender(), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.Extract(pt.Bytes("my string"), pt.Int(0), pt.Txn.sender())


def test_suffix_immediate():
    args = [pt.Bytes("my string"), pt.Int(1)]
    expr = pt.Suffix(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"my string"'),
            pt.TealOp(expr, pt.Op.extract, 1, 0),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_suffix_stack():
    my_string = "*" * 1024
    args = [pt.Bytes(my_string), pt.Int(257)]
    expr = pt.Suffix(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(args[1], pt.Op.int, 257),
            pt.TealOp(expr, pt.Op.dig, 1),
            pt.TealOp(expr, pt.Op.len),
            pt.TealOp(expr, pt.Op.substring3),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


@pytest.mark.parametrize("op", [pt.Op.extract3, pt.Op.substring3])
def test_startArg_not_int(op: pt.Op):
    my_string = "*" * 257
    add = pt.Add(pt.Int(254), pt.Int(2))
    args = [pt.Bytes(my_string), add, pt.Int(257)]

    def generate_expr() -> pt.Expr:
        match op:
            case pt.Op.extract3:
                return pt.Extract(args[0], args[1], args[2])
            case pt.Op.substring3:
                return pt.Substring(args[0], args[1], args[2])
            case _:
                raise Exception(f"Unsupported {op=}")

    expr = generate_expr()
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(pt.Int(254), pt.Op.int, 254),
            pt.TealOp(pt.Int(2), pt.Op.int, 2),
            pt.TealOp(add, pt.Op.add),
            pt.TealOp(args[2], pt.Op.int, 257),
            pt.TealOp(None, op),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    if op == pt.Op.extract3:
        with pytest.raises(pt.TealInputError):
            expr.__teal__(avm4Options)


@pytest.mark.parametrize("op", [pt.Op.extract3, pt.Op.substring3])
def test_endArg_not_int(op: pt.Op):
    my_string = "*" * 257
    add = pt.Add(pt.Int(254), pt.Int(3))
    args = [pt.Bytes(my_string), pt.Int(256), add]

    def generate_expr() -> pt.Expr:
        match op:
            case pt.Op.extract3:
                return pt.Extract(args[0], args[1], args[2])
            case pt.Op.substring3:
                return pt.Substring(args[0], args[1], args[2])
            case _:
                raise Exception(f"Unsupported {op=}")

    expr = generate_expr()
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{my_string}"'.format(my_string=my_string)),
            pt.TealOp(args[1], pt.Op.int, 256),
            pt.TealOp(pt.Int(254), pt.Op.int, 254),
            pt.TealOp(pt.Int(3), pt.Op.int, 3),
            pt.TealOp(add, pt.Op.add),
            pt.TealOp(None, op),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    if op == pt.Op.extract3:
        with pytest.raises(pt.TealInputError):
            expr.__teal__(avm4Options)


def test_suffix_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Suffix(pt.Int(0), pt.Int(0))

    with pytest.raises(pt.TealTypeError):
        pt.Suffix(pt.Bytes("my string"), pt.Txn.sender())
