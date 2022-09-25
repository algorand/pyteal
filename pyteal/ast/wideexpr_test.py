import pytest

import pyteal as pt

avm2Options = pt.CompileOptions(version=2)
avm3Options = pt.CompileOptions(version=3)
avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)


def test_addw():
    args = [pt.Int(2), pt.Int(3)]
    expr = pt.AddW(pt.Int(1), pt.Int(2))

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.addw),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


# TODO: test: test_addw_overload()


def test_addw_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AddW(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.AddW(pt.Txn.sender(), pt.Int(2))


def test_mulw():
    args = [pt.Int(3), pt.Int(8)]
    expr = pt.MulW(args[0], args[1])
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 3),
            pt.TealOp(args[1], pt.Op.int, 8),
            pt.TealOp(expr, pt.Op.mulw),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


# TODO: test: test_mulw_overload()


def test_mulw_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.MulW(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.MulW(pt.Txn.sender(), pt.Int(2))


# TODO: test: def test_modw_overload():
# TODO: test: def test_modw_invalid():


def test_expw():
    args = [pt.Int(2), pt.Int(9)]
    expr = pt.ExpW(args[0], args[1])
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 9),
            pt.TealOp(expr, pt.Op.expw),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


# TODO: test: def test_expw_overload():


def test_expw_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.ExpW(pt.Txn.receiver(), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.ExpW(pt.Int(2), pt.Txn.sender())


def test_expw_invalid_version():
    with pytest.raises(pt.TealInputError):
        pt.ExpW(pt.Int(2), pt.Int(2)).__teal__(avm3Options)  # needs >=4


def test_divmodw():
    args = [pt.Int(7), pt.Int(29), pt.Int(1), pt.Int(3)]
    expr = pt.DivModW(args[0], args[1], args[2], args[3])
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 7),
            pt.TealOp(args[1], pt.Op.int, 29),
            pt.TealOp(args[2], pt.Op.int, 1),
            pt.TealOp(args[3], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.divmodw),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_divmodw_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.DivModW(pt.Int(2), pt.Txn.receiver(), pt.Int(2), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.DivModW(pt.Int(2), pt.Int(2), pt.Txn.sender(), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.DivModW(pt.Int(2), pt.Int(2), pt.Int(2), pt.Txn.sender())


def test_divmodw_invalid_version():
    with pytest.raises(pt.TealInputError):
        pt.DivModW(pt.Int(2), pt.Int(2), pt.Int(2), pt.Int(2)).__teal__(
            avm3Options
        )  # needs >=4
