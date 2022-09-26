import pyteal as pt
import pytest

options = pt.CompileOptions()


def test_wide_from_int():
    creation_int_args = [
        0,
        1,
        8,
        232323,
        2**64 - 1,
        2**64,
        2**64 + 1,
        8 * 2**64 + 232323,
        2**128 - 1,
    ]
    expected_pyteal_int_values = [
        # bijection with creation_args
        [0, 0],
        [0, 1],
        [0, 8],
        [0, 232323],
        [0, 2**64 - 1],
        [1, 0],
        [1, 1],
        [8, 232323],
        [2**64 - 1, 2**64 - 1],
    ]

    for (idx, arg) in enumerate(creation_int_args):
        expr = pt.WideInt(arg)
        assert expr.type_of() == pt.TealType.none

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.int, expected_pyteal_int_values[idx][1]),
                pt.TealOp(expr.lo.store(), pt.Op.store, expr.lo),
                pt.TealOp(None, pt.Op.int, expected_pyteal_int_values[idx][0]),
                pt.TealOp(expr.hi.store(), pt.Op.store, expr.hi),
            ]
        )
        actual, _ = expr.__teal__(options)

        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_wide_from_expr_expr():
    creation_expr_args = [
        [pt.Int(2), pt.Int(3)],
        [pt.Int(8), pt.Int(232323)],
        [pt.Int(232323), pt.Int(8)],
        [pt.Int(2**64 - 1), pt.Int(2**64 - 1)],
    ]
    expected_pyteal_int_values = [
        # bijection with creation_args
        [2, 3],
        [8, 232323],
        [232323, 8],
        [2**64 - 1, 2**64 - 1],
    ]

    for (idx, args) in enumerate(creation_expr_args):
        expr = pt.WideInt(*args)
        assert expr.type_of() == pt.TealType.none

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.int, expected_pyteal_int_values[idx][1]),
                pt.TealOp(expr.lo.store(), pt.Op.store, expr.lo),
                pt.TealOp(None, pt.Op.int, expected_pyteal_int_values[idx][0]),
                pt.TealOp(expr.hi.store(), pt.Op.store, expr.hi),
            ]
        )
        actual, _ = expr.__teal__(options)

        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


# Failing cases
# TODO: test str        "foo",


def test_wide_int_creation_invalid():
    invalid_creation_args = [
        -1,
        -232323,
        2**128,
        2**128 + 1,
        2**128 + 232323,
        -(2**64) + 1,
        -8 * 2**64 + 232323,
        pt.Bytes("foo"),
        [pt.Bytes("foo"), pt.Int(3)],
        [pt.Int(2), pt.Bytes("foo")],
    ]
    for arg in invalid_creation_args:
        if isinstance(arg, list):
            with pytest.raises(pt.TealTypeError):
                pt.WideInt(*arg)
        else:
            with pytest.raises(pt.TealInputError):
                pt.WideInt(arg)
