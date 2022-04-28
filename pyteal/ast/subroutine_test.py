from itertools import product
import pytest
from typing import List

import pyteal as pt
from pyteal.ast.subroutine import evaluateSubroutine

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


def test_subroutine_definition_validate():
    """
    DFS through SubroutineDefinition.validate()'s logic
    """

    def mock_subroutine_definition(implementation):
        mock = pt.SubroutineDefinition(lambda: pt.Return(pt.Int(1)), pt.TealType.uint64)
        mock._validate()  # haven't failed with dummy implementation
        mock.implementation = implementation
        return mock

    not_callable = mock_subroutine_definition("I'm not callable")
    with pytest.raises(pt.TealInputError) as tie:
        not_callable._validate()

    assert tie.value == pt.TealInputError(
        "Input to SubroutineDefinition is not callable"
    )

    three_params = mock_subroutine_definition(lambda x, y, z: pt.Return(pt.Int(1)))
    two_inputs = [pt.TealType.uint64, pt.TealType.bytes]
    with pytest.raises(pt.TealInputError) as tie:
        three_params._validate(input_types=two_inputs)

    assert tie.value == pt.TealInputError(
        "Provided number of input_types (2) does not match detected number of parameters (3)"
    )

    params, anns, arg_types, byrefs = three_params._validate()
    assert len(params) == 3
    assert anns == {}
    assert all(at is pt.Expr for at in arg_types)
    assert byrefs == set()

    def bad_return_impl() -> str:
        return pt.Return(pt.Int(1))  # type: ignore

    bad_return = mock_subroutine_definition(bad_return_impl)
    with pytest.raises(pt.TealInputError) as tie:
        bad_return._validate()

    assert tie.value == pt.TealInputError(
        "Function has return of disallowed type <class 'str'>. Only Expr is allowed"
    )

    var_positional = mock_subroutine_definition(lambda *args: pt.Return(pt.Int(1)))
    with pytest.raises(pt.TealInputError) as tie:
        var_positional._validate()

    assert tie.value == pt.TealInputError(
        "Function has a parameter type that is not allowed in a subroutine: parameter args with type VAR_POSITIONAL"
    )

    kw_only = mock_subroutine_definition(lambda *, kw: pt.Return(pt.Int(1)))
    with pytest.raises(pt.TealInputError) as tie:
        kw_only._validate()

    assert tie.value == pt.TealInputError(
        "Function has a parameter type that is not allowed in a subroutine: parameter kw with type KEYWORD_ONLY"
    )

    var_keyword = mock_subroutine_definition(lambda **kw: pt.Return(pt.Int(1)))
    with pytest.raises(pt.TealInputError) as tie:
        var_keyword._validate()

    assert tie.value == pt.TealInputError(
        "Function has a parameter type that is not allowed in a subroutine: parameter kw with type VAR_KEYWORD"
    )

    param_default = mock_subroutine_definition(lambda x="niiiice": pt.Return(pt.Int(1)))
    with pytest.raises(pt.TealInputError) as tie:
        param_default._validate()

    assert tie.value == pt.TealInputError(
        "Function has a parameter with a default value, which is not allowed in a subroutine: x"
    )

    with pytest.raises(pt.TealInputError) as tie:
        three_params._validate(
            input_types=[pt.TealType.uint64, pt.Expr, pt.TealType.anytype]
        )

    assert tie.value == pt.TealInputError(
        "Function has input type <class 'pyteal.Expr'> for parameter y which is not a TealType"
    )

    # Now we get to _validate_parameter_type():
    one_vanilla = mock_subroutine_definition(lambda x: pt.Return(pt.Int(1)))

    params, anns, arg_types, byrefs = one_vanilla._validate()
    assert len(params) == 1
    assert anns == {}
    assert all(at is pt.Expr for at in arg_types)
    assert byrefs == set()

    def one_expr_impl(x: pt.Expr):
        return pt.Return(pt.Int(1))

    one_expr = mock_subroutine_definition(one_expr_impl)
    params, anns, arg_types, byrefs = one_expr._validate()
    assert len(params) == 1
    assert anns == {"x": pt.Expr}
    assert all(at is pt.Expr for at in arg_types)
    assert byrefs == set()

    def one_scratchvar_impl(x: pt.ScratchVar):
        return pt.Return(pt.Int(1))

    one_scratchvar = mock_subroutine_definition(one_scratchvar_impl)
    params, anns, arg_types, byrefs = one_scratchvar._validate()
    assert len(params) == 1
    assert anns == {"x": pt.ScratchVar}
    assert all(at is pt.ScratchVar for at in arg_types)
    assert byrefs == {"x"}

    def one_nontype_impl(x: "blahBlah"):  # type: ignore # noqa: F821
        return pt.Return(pt.Int(1))

    one_nontype = mock_subroutine_definition(one_nontype_impl)
    with pytest.raises(pt.TealInputError) as tie:
        one_nontype._validate()

    assert tie.value == pt.TealInputError(
        "Function has parameter x of declared type blahBlah which is not a class"
    )

    def one_dynscratchvar_impl(x: pt.DynamicScratchVar):
        return pt.Return(pt.Int(1))

    one_dynscratchvar = mock_subroutine_definition(one_dynscratchvar_impl)
    with pytest.raises(pt.TealInputError) as tie:
        one_dynscratchvar._validate()

    assert tie.value == pt.TealInputError(
        "Function has parameter x of disallowed type <class 'pyteal.DynamicScratchVar'>. Only the types (<class 'pyteal.Expr'>, <class 'pyteal.ScratchVar'>) are allowed"
    )

    # Now we're back to validate() and everything should be copacetic
    for x, y, z in product(pt.TealType, pt.TealType, pt.TealType):
        params, anns, arg_types, byrefs = three_params._validate(input_types=[x, y, z])
        assert len(params) == 3
        assert anns == {}
        assert all(at is pt.Expr for at in arg_types)
        assert byrefs == set()


def test_subroutine_invocation_param_types():
    def fnWithNoAnnotations(a, b):
        return pt.Return()

    def fnWithExprAnnotations(a: pt.Expr, b: pt.Expr) -> pt.Expr:
        return pt.Return()

    def fnWithSVAnnotations(a: pt.ScratchVar, b: pt.ScratchVar):
        return pt.Return()

    def fnWithMixedAnns1(a: pt.ScratchVar, b: pt.Expr) -> pt.Expr:
        return pt.Return()

    def fnWithMixedAnns2(a: pt.ScratchVar, b) -> pt.Expr:
        return pt.Return()

    def fnWithMixedAnns3(a: pt.Expr, b: pt.ScratchVar):
        return pt.Return()

    sv = pt.ScratchVar()
    x = pt.Int(42)
    s = pt.Bytes("hello")
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
        return pt.Bytes("helo")

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
