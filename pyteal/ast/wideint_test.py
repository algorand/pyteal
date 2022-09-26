import pyteal as pt
import pytest

options = pt.CompileOptions()


def test_wide_int_creation():
    creation_args = [
        0,
        1,
        8,
        232323,
        2**64 - 1,
        2**64,
        2**64 + 1,
        8 * 2**64 + 232323,
        2**128 - 1,
        [pt.Int(2), pt.Int(3)],
    ]
    expected_values_no_int = [
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
        [2, 3],
    ]

    for (idx, arg) in enumerate(creation_args):
        expr = pt.WideInt(*arg) if isinstance(arg, list) else pt.WideInt(arg)
        assert expr.type_of() == pt.TealType.none

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.int, expected_values_no_int[idx][1]),
                pt.TealOp(expr.lo.store(), pt.Op.store, expr.lo),
                pt.TealOp(None, pt.Op.int, expected_values_no_int[idx][0]),
                pt.TealOp(expr.hi.store(), pt.Op.store, expr.hi),
            ]
        )
        actual, _ = expr.__teal__(options)

        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


# Failing cases
def test_wide_int_creation_invalid():
    invalid_creation_args = [
        -1,
        -232323,
        2**128,
        2**128 + 1,
        2**128 + 232323,
        -(2**64) + 1,
        -8 * 2**64 + 232323,
        "foo",
        pt.Bytes("foo"),
        [pt.Bytes("foo"), pt.Int(3)],
        [pt.Int(2), pt.Bytes("foo")],
    ]
    for arg in invalid_creation_args:
        with pytest.raises((pt.TealInputError, pt.TealTypeError)):
            pt.WideInt(*arg) if isinstance(arg, list) else pt.WideInt(arg)
