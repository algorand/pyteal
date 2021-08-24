import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions(version=4)


def test_main_return():
    arg = Int(1)
    expr = Return(arg)
    assert expr.type_of() == TealType.none
    assert expr.has_return()

    expected = TealSimpleBlock([TealOp(arg, Op.int, 1), TealOp(expr, Op.return_)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_main_return_invalid():
    with pytest.raises(TealCompileError):
        Return(Txn.receiver()).__teal__(options)

    with pytest.raises(TealCompileError):
        Return().__teal__(options)


def test_subroutine_return_value():
    cases = (
        (TealType.uint64, Int(1), Op.int, 1),
        (TealType.bytes, Bytes("value"), Op.byte, '"value"'),
        (TealType.anytype, Int(1), Op.int, 1),
        (TealType.anytype, Bytes("value"), Op.byte, '"value"'),
    )

    for (tealType, value, op, opValue) in cases:
        expr = Return(value)

        def mySubroutine():
            return expr

        subroutine = SubroutineDefinition(mySubroutine, tealType)

        assert expr.type_of() == TealType.none
        assert expr.has_return()

        expected = TealSimpleBlock(
            [TealOp(value, op, opValue), TealOp(expr, Op.retsub)]
        )

        options.setSubroutine(subroutine)
        actual, _ = expr.__teal__(options)
        options.setSubroutine(None)

        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        assert actual == expected


def test_subroutine_return_value_invalid():
    cases = (
        (TealType.bytes, Int(1)),
        (TealType.uint64, Bytes("value")),
    )

    for (tealType, value) in cases:
        expr = Return(value)

        def mySubroutine():
            return expr

        subroutine = SubroutineDefinition(mySubroutine, tealType)

        options.setSubroutine(subroutine)
        with pytest.raises(TealCompileError):
            expr.__teal__(options)
        options.setSubroutine(None)


def test_subroutine_return_none():
    expr = Return()

    def mySubroutine():
        return expr

    subroutine = SubroutineDefinition(mySubroutine, TealType.none)

    assert expr.type_of() == TealType.none
    assert expr.has_return()

    expected = TealSimpleBlock([TealOp(expr, Op.retsub)])

    options.setSubroutine(subroutine)
    actual, _ = expr.__teal__(options)
    options.setSubroutine(None)

    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_subroutine_return_none_invalid():
    for value in (Int(1), Bytes("value")):
        expr = Return(value)

        def mySubroutine():
            return expr

        subroutine = SubroutineDefinition(mySubroutine, TealType.none)

        options.setSubroutine(subroutine)
        with pytest.raises(TealCompileError):
            expr.__teal__(options)
        options.setSubroutine(None)
