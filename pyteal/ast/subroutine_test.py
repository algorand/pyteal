from typing import List
import pytest

from .. import *
from .subroutine import evaluateSubroutine

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions, Return

options = CompileOptions(version=4)


def test_subroutine_definition():
    def fn0Args():
        return Return()

    def fn1Args(a1):
        return Return()

    def fn2Args(a1, a2):
        return Return()

    def fn10Args(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
        return Return()

    lam0Args = lambda: Return()
    lam1Args = lambda a1: Return()
    lam2Args = lambda a1, a2: Return()
    lam10Args = lambda a1, a2, a3, a4, a5, a6, a7, a8, a9, a10: Return()

    cases = (
        (fn0Args, 0, "fn0Args"),
        (fn1Args, 1, "fn1Args"),
        (fn2Args, 2, "fn2Args"),
        (fn10Args, 10, "fn10Args"),
        (lam0Args, 0, "<lambda>"),
        (lam1Args, 1, "<lambda>"),
        (lam2Args, 2, "<lambda>"),
        (lam10Args, 10, "<lambda>"),
    )

    for (fn, numArgs, name) in cases:
        definition = SubroutineDefinition(fn, TealType.none)
        assert definition.argumentCount() == numArgs
        assert definition.name() == name

        if numArgs > 0:
            with pytest.raises(TealInputError):
                definition.invoke([Int(1)] * (numArgs - 1))

        with pytest.raises(TealInputError):
            definition.invoke([Int(1)] * (numArgs + 1))

        if numArgs > 0:
            with pytest.raises(TealInputError):
                definition.invoke([1] * numArgs)

        args = [Int(1)] * numArgs
        invocation = definition.invoke(args)
        assert isinstance(invocation, SubroutineCall)
        assert invocation.subroutine is definition
        assert invocation.args == args


def test_subroutine_definition_invalid():
    def fnWithDefaults(a, b=None):
        return Return()

    def fnWithKeywordArgs(a, *, b):
        return Return()

    def fnWithVariableArgs(a, *b):
        return Return()

    cases = (
        1,
        None,
        fnWithDefaults,
        fnWithKeywordArgs,
        fnWithVariableArgs,
    )

    for case in cases:
        with pytest.raises(TealInputError):
            SubroutineDefinition(case, TealType.none)


def test_subroutine_declaration():
    cases = (
        (TealType.none, Return()),
        (TealType.uint64, Return(Int(1))),
        (TealType.uint64, Int(1)),
        (TealType.bytes, Bytes("value")),
        (TealType.anytype, App.globalGet(Bytes("key"))),
    )

    for (returnType, value) in cases:

        def mySubroutine():
            return value

        definition = SubroutineDefinition(mySubroutine, returnType)

        declaration = SubroutineDeclaration(definition, value)
        assert declaration.type_of() == value.type_of()
        assert declaration.has_return() == value.has_return()

        options.currentSubroutine = definition
        assert declaration.__teal__(options) == value.__teal__(options)
        options.setSubroutine(None)


def test_subroutine_call():
    def mySubroutine():
        return Return()

    returnTypes = (TealType.uint64, TealType.bytes, TealType.anytype, TealType.none)

    argCases = (
        [],
        [Int(1)],
        [Int(1), Bytes("value")],
    )

    for returnType in returnTypes:
        definition = SubroutineDefinition(mySubroutine, returnType)

        for args in argCases:
            expr = SubroutineCall(definition, args)

            assert expr.type_of() == returnType
            assert not expr.has_return()

            expected, _ = TealBlock.FromOp(
                options, TealOp(expr, Op.callsub, definition), *args
            )

            actual, _ = expr.__teal__(options)

            assert actual == expected


def test_decorator():
    assert callable(Subroutine)
    assert callable(Subroutine(TealType.anytype))

    @Subroutine(TealType.none)
    def mySubroutine(a):
        return Return()

    assert callable(mySubroutine)

    invocation = mySubroutine(Int(1))
    assert isinstance(invocation, SubroutineCall)

    with pytest.raises(TealInputError):
        mySubroutine()

    with pytest.raises(TealInputError):
        mySubroutine(Int(1), Int(2))

    with pytest.raises(TealInputError):
        mySubroutine(Pop(Int(1)))

    with pytest.raises(TealInputError):
        mySubroutine(1)

    with pytest.raises(TealInputError):
        mySubroutine(a=Int(1))


def test_evaluate_subroutine_no_args():
    cases = (
        (TealType.none, Return()),
        (TealType.uint64, Int(1) + Int(2)),
        (TealType.uint64, Return(Int(1) + Int(2))),
        (TealType.bytes, Bytes("value")),
        (TealType.bytes, Return(Bytes("value"))),
    )

    for (returnType, returnValue) in cases:

        def mySubroutine():
            return returnValue

        definition = SubroutineDefinition(mySubroutine, returnType)

        declaration = evaluateSubroutine(definition)
        assert isinstance(declaration, SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == returnValue.type_of()
        assert declaration.has_return() == returnValue.has_return()

        options.setSubroutine(definition)
        expected, _ = Seq([returnValue]).__teal__(options)

        actual, _ = declaration.__teal__(options)
        options.setSubroutine(None)
        assert actual == expected


def test_evaluate_subroutine_1_arg():
    cases = (
        (TealType.none, Return()),
        (TealType.uint64, Int(1) + Int(2)),
        (TealType.uint64, Return(Int(1) + Int(2))),
        (TealType.bytes, Bytes("value")),
        (TealType.bytes, Return(Bytes("value"))),
    )

    for (returnType, returnValue) in cases:
        argSlots: List[ScratchSlot] = []

        def mySubroutine(a1):
            assert isinstance(a1, ScratchLoad)
            argSlots.append(a1.slot)
            return returnValue

        definition = SubroutineDefinition(mySubroutine, returnType)

        declaration = evaluateSubroutine(definition)
        assert isinstance(declaration, SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == returnValue.type_of()
        assert declaration.has_return() == returnValue.has_return()

        assert isinstance(declaration.body, Seq)
        assert len(declaration.body.args) == 2

        assert isinstance(declaration.body.args[0], ScratchStackStore)

        assert declaration.body.args[0].slot is argSlots[-1]

        options.setSubroutine(definition)
        expected, _ = Seq([declaration.body.args[0], returnValue]).__teal__(options)

        actual, _ = declaration.__teal__(options)
        options.setSubroutine(None)
        assert actual == expected


def test_evaluate_subroutine_2_args():
    cases = (
        (TealType.none, Return()),
        (TealType.uint64, Int(1) + Int(2)),
        (TealType.uint64, Return(Int(1) + Int(2))),
        (TealType.bytes, Bytes("value")),
        (TealType.bytes, Return(Bytes("value"))),
    )

    for (returnType, returnValue) in cases:
        argSlots: List[ScratchSlot] = []

        def mySubroutine(a1, a2):
            assert isinstance(a1, ScratchLoad)
            argSlots.append(a1.slot)
            assert isinstance(a2, ScratchLoad)
            argSlots.append(a2.slot)
            return returnValue

        definition = SubroutineDefinition(mySubroutine, returnType)

        declaration = evaluateSubroutine(definition)
        assert isinstance(declaration, SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == returnValue.type_of()
        assert declaration.has_return() == returnValue.has_return()

        assert isinstance(declaration.body, Seq)
        assert len(declaration.body.args) == 3

        assert isinstance(declaration.body.args[0], ScratchStackStore)
        assert isinstance(declaration.body.args[1], ScratchStackStore)

        assert declaration.body.args[0].slot is argSlots[-1]
        assert declaration.body.args[1].slot is argSlots[-2]

        options.setSubroutine(definition)
        expected, _ = Seq(
            [declaration.body.args[0], declaration.body.args[1], returnValue]
        ).__teal__(options)

        actual, _ = declaration.__teal__(options)
        options.setSubroutine(None)
        assert actual == expected


def test_evaluate_subroutine_10_args():
    cases = (
        (TealType.none, Return()),
        (TealType.uint64, Int(1) + Int(2)),
        (TealType.uint64, Return(Int(1) + Int(2))),
        (TealType.bytes, Bytes("value")),
        (TealType.bytes, Return(Bytes("value"))),
    )

    for (returnType, returnValue) in cases:
        argSlots: List[ScratchSlot] = []

        def mySubroutine(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
            for a in (a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
                assert isinstance(a, ScratchLoad)
                argSlots.append(a.slot)
            return returnValue

        definition = SubroutineDefinition(mySubroutine, returnType)

        declaration = evaluateSubroutine(definition)
        assert isinstance(declaration, SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == returnValue.type_of()
        assert declaration.has_return() == returnValue.has_return()

        assert isinstance(declaration.body, Seq)
        assert len(declaration.body.args) == 11

        for i in range(10):
            assert isinstance(declaration.body.args[i], ScratchStackStore)

        for i in range(10):
            assert declaration.body.args[i].slot is argSlots[-i - 1]

        options.setSubroutine(definition)
        expected, _ = Seq(declaration.body.args[:10] + [returnValue]).__teal__(options)

        actual, _ = declaration.__teal__(options)
        options.setSubroutine(None)
        assert actual == expected
