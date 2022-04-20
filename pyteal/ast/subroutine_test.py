from typing import List, Literal
import pytest

import pyteal as pt
from .subroutine import evaluateSubroutine

options = pt.CompileOptions(version=4)


def test_subroutine_definition():
    def fn0Args():
        return pt.Return()

    def fn1Args(a1):
        return pt.Return()

    def fn2Args(a1, a2):
        return pt.Return()

    def fn10Args(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
        return pt.Return()

    lam0Args = lambda: pt.Return()  # noqa: E731
    lam1Args = lambda a1: pt.Return()  # noqa: E731
    lam2Args = lambda a1, a2: pt.Return()  # noqa: E731
    lam10Args = (
        lambda a1, a2, a3, a4, a5, a6, a7, a8, a9, a10: pt.Return()
    )  # noqa: E731

    def fnWithExprAnnotations(a: pt.Expr, b: pt.Expr) -> pt.Expr:
        return pt.Return()

    def fnWithOnlyReturnExprAnnotations(a, b) -> pt.Expr:
        return pt.Return()

    def fnWithOnlyArgExprAnnotations(a: pt.Expr, b: pt.Expr):
        return pt.Return()

    def fnWithPartialExprAnnotations(a, b: pt.Expr) -> pt.Expr:
        return pt.Return()

    cases = (
        (fn0Args, 0, "fn0Args"),
        (fn1Args, 1, "fn1Args"),
        (fn2Args, 2, "fn2Args"),
        (fn10Args, 10, "fn10Args"),
        (lam0Args, 0, "<lambda>"),
        (lam1Args, 1, "<lambda>"),
        (lam2Args, 2, "<lambda>"),
        (lam10Args, 10, "<lambda>"),
        (fnWithExprAnnotations, 2, "fnWithExprAnnotations"),
        (fnWithOnlyReturnExprAnnotations, 2, "fnWithOnlyReturnExprAnnotations"),
        (fnWithOnlyArgExprAnnotations, 2, "fnWithOnlyArgExprAnnotations"),
        (fnWithPartialExprAnnotations, 2, "fnWithPartialExprAnnotations"),
    )

    for (fn, numArgs, name) in cases:
        definition = pt.SubroutineDefinition(fn, pt.TealType.none)
        assert definition.argumentCount() == numArgs
        assert definition.name() == name

        if numArgs > 0:
            with pytest.raises(pt.TealInputError):
                definition.invoke([pt.Int(1)] * (numArgs - 1))

        with pytest.raises(pt.TealInputError):
            definition.invoke([pt.Int(1)] * (numArgs + 1))

        if numArgs > 0:
            with pytest.raises(pt.TealInputError):
                definition.invoke([1] * numArgs)

        args = [pt.Int(1)] * numArgs
        invocation = definition.invoke(args)
        assert isinstance(invocation, pt.SubroutineCall)
        assert invocation.subroutine is definition
        assert invocation.args == args


def test_subroutine_invocation_param_types():
    def fnWithNoAnnotations(a, b):
        return pt.Return()

    def fnWithExprAnnotations(a: pt.Expr, b: pt.Expr) -> pt.Expr:
        return pt.Return()

    def fnWithSVAnnotations(a: pt.ScratchVar, b: pt.ScratchVar):
        return pt.Return()

    def fnWithABIAnnotations(
        a: pt.abi.Byte,
        b: pt.abi.StaticArray[pt.abi.Uint32, Literal[10]],
        c: pt.abi.DynamicArray[pt.abi.Bool],
    ):
        return pt.Return()

    def fnWithMixedAnns1(a: pt.ScratchVar, b: pt.Expr) -> pt.Expr:
        return pt.Return()

    def fnWithMixedAnns2(a: pt.ScratchVar, b) -> pt.Expr:
        return pt.Return()

    def fnWithMixedAnns3(a: pt.Expr, b: pt.ScratchVar):
        return pt.Return()

    def fnWithMixedAnns4(a: pt.ScratchVar, b, c: pt.abi.Uint16) -> pt.Expr:
        return pt.Return()

    sv = pt.ScratchVar()
    x = pt.Int(42)
    s = pt.Bytes("hello")
    av_u16 = pt.abi.Uint16()
    av_bool_dym_arr = pt.abi.DynamicArray(pt.abi.BoolTypeSpec())
    av_u32_static_arr = pt.abi.StaticArray(pt.abi.Uint32TypeSpec(), 10)
    av_bool = pt.abi.Bool()
    av_byte = pt.abi.Byte()

    cases = [
        ("vanilla 1", fnWithNoAnnotations, [x, s], None),
        ("vanilla 2", fnWithNoAnnotations, [x, x], None),
        ("vanilla no sv's allowed 1", fnWithNoAnnotations, [x, sv], pt.TealInputError),
        ("exprs 1", fnWithExprAnnotations, [x, s], None),
        ("exprs 2", fnWithExprAnnotations, [x, x], None),
        ("exprs no sv's allowed 1", fnWithExprAnnotations, [x, sv], pt.TealInputError),
        ("all sv's 1", fnWithSVAnnotations, [sv, sv], None),
        ("all sv's but strings", fnWithSVAnnotations, [s, s], pt.TealInputError),
        ("all sv's but ints", fnWithSVAnnotations, [x, x], pt.TealInputError),
        (
            "all abi's 1",
            fnWithABIAnnotations,
            [av_byte, av_u32_static_arr, av_bool_dym_arr],
            None,
        ),
        (
            "all abi's but ints 1",
            fnWithABIAnnotations,
            [x, av_u32_static_arr, av_bool_dym_arr],
            pt.TealInputError,
        ),
        (
            "all abi's but ints 2",
            fnWithABIAnnotations,
            [x, av_u32_static_arr, x],
            pt.TealInputError,
        ),
        ("all abi's but ints 3", fnWithABIAnnotations, [x, x, x], pt.TealInputError),
        (
            "all abi's but sv's 1",
            fnWithABIAnnotations,
            [sv, av_u32_static_arr, av_bool_dym_arr],
            pt.TealInputError,
        ),
        (
            "all abi's but sv's 2",
            fnWithABIAnnotations,
            [av_byte, av_u32_static_arr, sv],
            pt.TealInputError,
        ),
        (
            "all abi's but sv's 3",
            fnWithABIAnnotations,
            [av_byte, sv, av_u32_static_arr],
            pt.TealInputError,
        ),
        (
            "all abi's but wrong typed 1",
            fnWithABIAnnotations,
            [av_u32_static_arr, av_u32_static_arr, av_bool_dym_arr],
            pt.TealInputError,
        ),
        (
            "all abi's but wrong typed 2",
            fnWithABIAnnotations,
            [av_bool, av_bool_dym_arr, av_u16],
            pt.TealInputError,
        ),
        (
            "all abi's but wrong typed 3",
            fnWithABIAnnotations,
            [av_u16, av_bool, av_byte],
            pt.TealInputError,
        ),
        ("mixed1 copacetic", fnWithMixedAnns1, [sv, x], None),
        ("mixed1 flipped", fnWithMixedAnns1, [x, sv], pt.TealInputError),
        ("mixed1 missing the sv", fnWithMixedAnns1, [x, s], pt.TealInputError),
        ("mixed1 missing the non-sv", fnWithMixedAnns1, [sv, sv], pt.TealInputError),
        ("mixed2 copacetic", fnWithMixedAnns2, [sv, x], None),
        ("mixed2 flipped", fnWithMixedAnns2, [x, sv], pt.TealInputError),
        ("mixed2 missing the sv", fnWithMixedAnns2, [x, s], pt.TealInputError),
        ("mixed2 missing the non-sv", fnWithMixedAnns2, [sv, sv], pt.TealInputError),
        ("mixed3 copacetic", fnWithMixedAnns3, [s, sv], None),
        ("mixed3 flipped", fnWithMixedAnns3, [sv, x], pt.TealInputError),
        ("mixed3 missing the sv", fnWithMixedAnns3, [x, s], pt.TealInputError),
        ("mixed anno", fnWithMixedAnns4, [sv, x, av_u16], None),
        (
            "mixed anno but wrong typed 1",
            fnWithMixedAnns4,
            [av_byte, x, av_u16],
            pt.TealInputError,
        ),
        (
            "mixed anno but wrong typed 2",
            fnWithMixedAnns4,
            [sv, av_byte, sv],
            pt.TealInputError,
        ),
        (
            "mixed anno but wrong typed 3",
            fnWithMixedAnns4,
            [sv, x, av_byte],
            pt.TealInputError,
        ),
    ]
    for case_name, fn, args, err in cases:
        definition = pt.SubroutineDefinition(fn, pt.TealType.none)
        assert definition.argumentCount() == len(args), case_name
        assert definition.name() == fn.__name__, case_name

        if err is None:
            assert len(definition.by_ref_args) == len(
                [x for x in args if isinstance(x, pt.ScratchVar)]
            ), case_name

            invocation = definition.invoke(args)
            assert isinstance(invocation, pt.SubroutineCall), case_name
            assert invocation.subroutine is definition, case_name
            assert invocation.args == args, case_name
            assert invocation.has_return() is False, case_name

        else:
            try:
                with pytest.raises(err):
                    definition.invoke(args)
            except Exception as e:
                assert (
                    not e
                ), f"EXPECTED ERROR of type {err}. encountered unexpected error during invocation case <{case_name}>: {e}"


def test_subroutine_definition_invalid():
    def fnWithDefaults(a, b=None):
        return pt.Return()

    def fnWithKeywordArgs(a, *, b):
        return pt.Return()

    def fnWithVariableArgs(a, *b):
        return pt.Return()

    def fnWithNonExprReturnAnnotation(a, b) -> pt.TealType.uint64:
        return pt.Return()

    def fnWithNonExprParamAnnotation(a, b: pt.TealType.uint64):
        return pt.Return()

    def fnWithScratchVarSubclass(a, b: pt.DynamicScratchVar):
        return pt.Return()

    def fnReturningExprSubclass(a: pt.ScratchVar, b: pt.Expr) -> pt.Return:
        return pt.Return()

    def fnWithMixedAnns4AndBytesReturn(a: pt.Expr, b: pt.ScratchVar) -> pt.Bytes:
        return pt.Bytes("hello uwu")

    def fnWithMixedAnnsABIRet1(
        a: pt.Expr, b: pt.ScratchVar, c: pt.abi.Uint16
    ) -> pt.abi.StaticArray[pt.abi.Uint32, Literal[10]]:
        return pt.abi.StaticArray(pt.abi.Uint32TypeSpec(), 10)

    def fnWithMixedAnnsABIRet2(
        a: pt.Expr, b: pt.abi.Byte, c: pt.ScratchVar
    ) -> pt.abi.Uint64:
        return pt.abi.Uint64()

    cases = (
        (1, "TealInputError('Input to SubroutineDefinition is not callable'"),
        (None, "TealInputError('Input to SubroutineDefinition is not callable'"),
        (
            fnWithDefaults,
            "TealInputError('Function has a parameter with a default value, which is not allowed in a subroutine: b'",
        ),
        (
            fnWithKeywordArgs,
            "TealInputError('Function has a parameter type that is not allowed in a subroutine: parameter b with type",
        ),
        (
            fnWithVariableArgs,
            "TealInputError('Function has a parameter type that is not allowed in a subroutine: parameter b with type",
        ),
        (
            fnWithNonExprReturnAnnotation,
            "Function has return of disallowed type TealType.uint64. Only Expr is allowed",
        ),
        (
            fnWithNonExprParamAnnotation,
            "Function has parameter b of declared type TealType.uint64 which is not a class",
        ),
        (
            fnWithScratchVarSubclass,
            "Function has parameter b of disallowed type <class 'pyteal.DynamicScratchVar'>",
        ),
        (
            fnReturningExprSubclass,
            "Function has return of disallowed type <class 'pyteal.Return'>",
        ),
        (
            fnWithMixedAnns4AndBytesReturn,
            "Function has return of disallowed type <class 'pyteal.Bytes'>",
        ),
        (
            fnWithMixedAnnsABIRet1,
            "Function has return of disallowed type pyteal.StaticArray[pyteal.Uint32, typing.Literal[10]]. "
            "Only Expr is allowed",
        ),
        (
            fnWithMixedAnnsABIRet2,
            "Function has return of disallowed type <class 'pyteal.Uint64'>. Only Expr is allowed",
        ),
    )

    for fn, msg in cases:
        with pytest.raises(pt.TealInputError) as e:
            print(f"case=[{msg}]")
            pt.SubroutineDefinition(fn, pt.TealType.none)

        assert msg in str(e), "failed for case [{}]".format(fn.__name__)


def test_subroutine_declaration():
    cases = (
        (pt.TealType.none, pt.Return()),
        (pt.TealType.uint64, pt.Return(pt.Int(1))),
        (pt.TealType.uint64, pt.Int(1)),
        (pt.TealType.bytes, pt.Bytes("value")),
        (pt.TealType.anytype, pt.App.globalGet(pt.Bytes("key"))),
    )

    for (returnType, value) in cases:

        def mySubroutine():
            return value

        definition = pt.SubroutineDefinition(mySubroutine, returnType)

        declaration = pt.SubroutineDeclaration(definition, value)
        assert declaration.type_of() == value.type_of()
        assert declaration.has_return() == value.has_return()

        options.currentSubroutine = definition
        assert declaration.__teal__(options) == value.__teal__(options)
        options.setSubroutine(None)


def test_subroutine_call():
    def mySubroutine():
        return pt.Return()

    returnTypes = (
        pt.TealType.uint64,
        pt.TealType.bytes,
        pt.TealType.anytype,
        pt.TealType.none,
    )

    argCases = (
        [],
        [pt.Int(1)],
        [pt.Int(1), pt.Bytes("value")],
    )

    for returnType in returnTypes:
        definition = pt.SubroutineDefinition(mySubroutine, returnType)

        for args in argCases:
            expr = pt.SubroutineCall(definition, args)

            assert expr.type_of() == returnType
            assert not expr.has_return()

            expected, _ = pt.TealBlock.FromOp(
                options, pt.TealOp(expr, pt.Op.callsub, definition), *args
            )

            actual, _ = expr.__teal__(options)

            assert actual == expected


def test_decorator():
    assert callable(pt.Subroutine)
    assert callable(pt.Subroutine(pt.TealType.anytype))

    @pt.Subroutine(pt.TealType.none)
    def mySubroutine(a):
        return pt.Return()

    assert isinstance(mySubroutine, pt.SubroutineFnWrapper)

    invocation = mySubroutine(pt.Int(1))
    assert isinstance(invocation, pt.SubroutineCall)

    with pytest.raises(pt.TealInputError):
        mySubroutine()

    with pytest.raises(pt.TealInputError):
        mySubroutine(pt.Int(1), pt.Int(2))

    with pytest.raises(pt.TealInputError):
        mySubroutine(pt.Pop(pt.Int(1)))

    with pytest.raises(pt.TealInputError):
        mySubroutine(1)

    with pytest.raises(pt.TealInputError):
        mySubroutine(a=pt.Int(1))


def test_evaluate_subroutine_no_args():
    cases = (
        (pt.TealType.none, pt.Return()),
        (pt.TealType.uint64, pt.Int(1) + pt.Int(2)),
        (pt.TealType.uint64, pt.Return(pt.Int(1) + pt.Int(2))),
        (pt.TealType.bytes, pt.Bytes("value")),
        (pt.TealType.bytes, pt.Return(pt.Bytes("value"))),
    )

    for (returnType, returnValue) in cases:

        def mySubroutine():
            return returnValue

        definition = pt.SubroutineDefinition(mySubroutine, returnType)

        declaration = evaluateSubroutine(definition)
        assert isinstance(declaration, pt.SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == returnValue.type_of()
        assert declaration.has_return() == returnValue.has_return()

        options.setSubroutine(definition)
        expected, _ = pt.Seq([returnValue]).__teal__(options)

        actual, _ = declaration.__teal__(options)
        options.setSubroutine(None)
        assert actual == expected


def test_evaluate_subroutine_1_arg():
    cases = (
        (pt.TealType.none, pt.Return()),
        (pt.TealType.uint64, pt.Int(1) + pt.Int(2)),
        (pt.TealType.uint64, pt.Return(pt.Int(1) + pt.Int(2))),
        (pt.TealType.bytes, pt.Bytes("value")),
        (pt.TealType.bytes, pt.Return(pt.Bytes("value"))),
    )

    for (returnType, returnValue) in cases:
        argSlots: List[pt.ScratchSlot] = []

        def mySubroutine(a1):
            assert isinstance(a1, pt.ScratchLoad)
            argSlots.append(a1.slot)
            return returnValue

        definition = pt.SubroutineDefinition(mySubroutine, returnType)

        declaration = evaluateSubroutine(definition)
        assert isinstance(declaration, pt.SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == returnValue.type_of()
        assert declaration.has_return() == returnValue.has_return()

        assert isinstance(declaration.body, pt.Seq)
        assert len(declaration.body.args) == 2

        assert isinstance(declaration.body.args[0], pt.ScratchStackStore)

        assert declaration.body.args[0].slot is argSlots[-1]

        options.setSubroutine(definition)
        expected, _ = pt.Seq([declaration.body.args[0], returnValue]).__teal__(options)

        actual, _ = declaration.__teal__(options)
        options.setSubroutine(None)
        assert actual == expected


def test_evaluate_subroutine_2_args():
    cases = (
        (pt.TealType.none, pt.Return()),
        (pt.TealType.uint64, pt.Int(1) + pt.Int(2)),
        (pt.TealType.uint64, pt.Return(pt.Int(1) + pt.Int(2))),
        (pt.TealType.bytes, pt.Bytes("value")),
        (pt.TealType.bytes, pt.Return(pt.Bytes("value"))),
    )

    for (returnType, returnValue) in cases:
        argSlots: List[pt.ScratchSlot] = []

        def mySubroutine(a1, a2):
            assert isinstance(a1, pt.ScratchLoad)
            argSlots.append(a1.slot)
            assert isinstance(a2, pt.ScratchLoad)
            argSlots.append(a2.slot)
            return returnValue

        definition = pt.SubroutineDefinition(mySubroutine, returnType)

        declaration = evaluateSubroutine(definition)
        assert isinstance(declaration, pt.SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == returnValue.type_of()
        assert declaration.has_return() == returnValue.has_return()

        assert isinstance(declaration.body, pt.Seq)
        assert len(declaration.body.args) == 3

        assert isinstance(declaration.body.args[0], pt.ScratchStackStore)
        assert isinstance(declaration.body.args[1], pt.ScratchStackStore)

        assert declaration.body.args[0].slot is argSlots[-1]
        assert declaration.body.args[1].slot is argSlots[-2]

        options.setSubroutine(definition)
        expected, _ = pt.Seq(
            [declaration.body.args[0], declaration.body.args[1], returnValue]
        ).__teal__(options)

        actual, _ = declaration.__teal__(options)
        options.setSubroutine(None)
        assert actual == expected


def test_evaluate_subroutine_10_args():
    cases = (
        (pt.TealType.none, pt.Return()),
        (pt.TealType.uint64, pt.Int(1) + pt.Int(2)),
        (pt.TealType.uint64, pt.Return(pt.Int(1) + pt.Int(2))),
        (pt.TealType.bytes, pt.Bytes("value")),
        (pt.TealType.bytes, pt.Return(pt.Bytes("value"))),
    )

    for (returnType, returnValue) in cases:
        argSlots: List[pt.ScratchSlot] = []

        def mySubroutine(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
            for a in (a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
                assert isinstance(a, pt.ScratchLoad)
                argSlots.append(a.slot)
            return returnValue

        definition = pt.SubroutineDefinition(mySubroutine, returnType)

        declaration = evaluateSubroutine(definition)
        assert isinstance(declaration, pt.SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == returnValue.type_of()
        assert declaration.has_return() == returnValue.has_return()

        assert isinstance(declaration.body, pt.Seq)
        assert len(declaration.body.args) == 11

        for i in range(10):
            assert isinstance(declaration.body.args[i], pt.ScratchStackStore)

        for i in range(10):
            assert declaration.body.args[i].slot is argSlots[-i - 1]

        options.setSubroutine(definition)
        expected, _ = pt.Seq(declaration.body.args[:10] + [returnValue]).__teal__(
            options
        )

        actual, _ = declaration.__teal__(options)
        options.setSubroutine(None)
        assert actual == expected
