import pytest

import pyteal as pt

options = pt.CompileOptions(version=4)


def test_main_return():
    arg = pt.Int(1)
    expr = pt.Return(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.has_return()

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 1), pt.TealOp(expr, pt.Op.return_)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_main_return_invalid():
    with pytest.raises(pt.TealCompileError):
        pt.Return(pt.Txn.receiver()).__teal__(options)

    with pytest.raises(pt.TealCompileError):
        pt.Return().__teal__(options)


def test_subroutine_return_value():
    cases = (
        (pt.TealType.uint64, pt.Int(1), pt.Op.int, 1),
        (pt.TealType.bytes, pt.Bytes("value"), pt.Op.byte, '"value"'),
        (pt.TealType.anytype, pt.Int(1), pt.Op.int, 1),
        (pt.TealType.anytype, pt.Bytes("value"), pt.Op.byte, '"value"'),
    )

    for (tealType, value, op, opValue) in cases:
        expr = pt.Return(value)

        def mySubroutine():
            return expr

        subroutine = pt.SubroutineDefinition(mySubroutine, tealType)

        assert expr.type_of() == pt.TealType.none
        assert expr.has_return()

        expected = pt.TealSimpleBlock(
            [pt.TealOp(value, op, opValue), pt.TealOp(expr, pt.Op.retsub)]
        )

        options.setSubroutine(subroutine)
        actual, _ = expr.__teal__(options)
        options.setSubroutine(None)

        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        assert actual == expected


def test_subroutine_return_value_invalid():
    cases = (
        (pt.TealType.bytes, pt.Int(1)),
        (pt.TealType.uint64, pt.Bytes("value")),
    )

    for (tealType, value) in cases:
        expr = pt.Return(value)

        def mySubroutine():
            return expr

        subroutine = pt.SubroutineDefinition(mySubroutine, tealType)

        options.setSubroutine(subroutine)
        with pytest.raises(pt.TealCompileError):
            expr.__teal__(options)
        options.setSubroutine(None)


def test_subroutine_return_none():
    expr = pt.Return()

    def mySubroutine():
        return expr

    subroutine = pt.SubroutineDefinition(mySubroutine, pt.TealType.none)

    assert expr.type_of() == pt.TealType.none
    assert expr.has_return()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.retsub)])

    options.setSubroutine(subroutine)
    actual, _ = expr.__teal__(options)
    options.setSubroutine(None)

    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_subroutine_return_none_invalid():
    for value in (pt.Int(1), pt.Bytes("value")):
        expr = pt.Return(value)

        def mySubroutine():
            return expr

        subroutine = pt.SubroutineDefinition(mySubroutine, pt.TealType.none)

        options.setSubroutine(subroutine)
        with pytest.raises(pt.TealCompileError):
            expr.__teal__(options)
        options.setSubroutine(None)
