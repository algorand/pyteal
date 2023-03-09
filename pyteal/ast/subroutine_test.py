from itertools import product
from typing import Callable, Literal, Optional, cast
from inspect import signature

import pytest
from dataclasses import dataclass

import pyteal as pt
from pyteal.ast.frame import FrameVar, Proto, ProtoStackLayout, FrameBury, FrameDig
from pyteal.ast.subroutine import ABIReturnSubroutine, SubroutineEval
from pyteal.compiler.compiler import FRAME_POINTERS_VERSION

options = pt.CompileOptions(version=5)
options_v8 = pt.CompileOptions(version=8)


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

    for fn, numArgs, name in cases:
        definition = pt.SubroutineDefinition(fn, pt.TealType.none)
        assert definition.argument_count() == numArgs
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


@dataclass
class ABISubroutineTC:
    definition: pt.ABIReturnSubroutine
    arg_instances: list[pt.Expr | pt.abi.BaseType]
    name: str
    ret_type: str | pt.abi.TypeSpec
    signature: Optional[str]


def test_abi_subroutine_definition():
    @pt.ABIReturnSubroutine
    def fn_0arg_0ret() -> pt.Expr:
        return pt.Return()

    @pt.ABIReturnSubroutine
    def fn_0arg_uint64_ret(*, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(1)

    @pt.ABIReturnSubroutine
    def fn_1arg_0ret(a: pt.abi.Uint64) -> pt.Expr:
        return pt.Return()

    @pt.ABIReturnSubroutine
    def fn_1arg_1ret(a: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a)

    @pt.ABIReturnSubroutine
    def fn_2arg_0ret(
        a: pt.abi.Uint64, b: pt.abi.StaticArray[pt.abi.Byte, Literal[10]]
    ) -> pt.Expr:
        return pt.Return()

    @pt.ABIReturnSubroutine
    def fn_2arg_1ret(
        a: pt.abi.Uint64,
        b: pt.abi.StaticArray[pt.abi.Byte, Literal[10]],
        *,
        output: pt.abi.Byte,
    ) -> pt.Expr:
        return output.set(b[a.get() % pt.Int(10)])

    @pt.ABIReturnSubroutine
    def fn_2arg_1ret_with_expr(
        a: pt.Expr,
        b: pt.abi.StaticArray[pt.abi.Byte, Literal[10]],
        *,
        output: pt.abi.Byte,
    ) -> pt.Expr:
        return output.set(b[a % pt.Int(10)])

    @pt.ABIReturnSubroutine
    def fn_w_tuple1arg(
        a: pt.Expr,
        b: pt.abi.Tuple1[pt.abi.Byte],
        *,
        output: pt.abi.Byte,
    ) -> pt.Expr:
        return output.set(pt.Int(1))

    cases = (
        ABISubroutineTC(fn_0arg_0ret, [], "fn_0arg_0ret", "void", "fn_0arg_0ret()void"),
        ABISubroutineTC(
            fn_0arg_uint64_ret,
            [],
            "fn_0arg_uint64_ret",
            pt.abi.Uint64TypeSpec(),
            "fn_0arg_uint64_ret()uint64",
        ),
        ABISubroutineTC(
            fn_1arg_0ret,
            [pt.abi.Uint64()],
            "fn_1arg_0ret",
            "void",
            "fn_1arg_0ret(uint64)void",
        ),
        ABISubroutineTC(
            fn_1arg_1ret,
            [pt.abi.Uint64()],
            "fn_1arg_1ret",
            pt.abi.Uint64TypeSpec(),
            "fn_1arg_1ret(uint64)uint64",
        ),
        ABISubroutineTC(
            fn_2arg_0ret,
            [
                pt.abi.Uint64(),
                pt.abi.StaticArray(
                    pt.abi.StaticArrayTypeSpec(pt.abi.ByteTypeSpec(), 10)
                ),
            ],
            "fn_2arg_0ret",
            "void",
            "fn_2arg_0ret(uint64,byte[10])void",
        ),
        ABISubroutineTC(
            fn_2arg_1ret,
            [
                pt.abi.Uint64(),
                pt.abi.StaticArray(
                    pt.abi.StaticArrayTypeSpec(pt.abi.ByteTypeSpec(), 10)
                ),
            ],
            "fn_2arg_1ret",
            pt.abi.ByteTypeSpec(),
            "fn_2arg_1ret(uint64,byte[10])byte",
        ),
        ABISubroutineTC(
            fn_2arg_1ret_with_expr,
            [
                pt.Int(5),
                pt.abi.StaticArray(
                    pt.abi.StaticArrayTypeSpec(pt.abi.ByteTypeSpec(), 10)
                ),
            ],
            "fn_2arg_1ret_with_expr",
            pt.abi.ByteTypeSpec(),
            None,
        ),
        ABISubroutineTC(
            fn_w_tuple1arg,
            [
                pt.Int(5),
                pt.abi.make(pt.abi.Tuple1[pt.abi.Byte]),
            ],
            "fn_w_tuple1arg",
            pt.abi.ByteTypeSpec(),
            None,
        ),
    )

    for case in cases:
        assert case.definition.subroutine.argument_count() == len(case.arg_instances)
        assert case.definition.name() == case.name

        if len(case.arg_instances) > 0:
            with pytest.raises(pt.TealInputError):
                case.definition(*case.arg_instances[:-1])

        with pytest.raises(pt.TealInputError):
            case.definition(*(case.arg_instances + [pt.abi.Uint64()]))

        assert case.definition.type_of() == case.ret_type
        invoked = case.definition(*case.arg_instances)
        assert isinstance(
            invoked, (pt.Expr if case.ret_type == "void" else pt.abi.ReturnedValue)
        )
        assert case.definition.is_abi_routable() == all(
            map(lambda x: isinstance(x, pt.abi.BaseType), case.arg_instances)
        )

        if case.definition.is_abi_routable():
            assert case.definition.method_signature() == cast(str, case.signature)
        else:
            with pytest.raises(pt.TealInputError):
                case.definition.method_signature()


def test_subroutine_return_reference():
    @ABIReturnSubroutine
    def invalid_ret_type(*, output: pt.abi.Account):
        return output.decode(pt.Bytes(b"\x00"))

    with pytest.raises(pt.TealInputError):
        invalid_ret_type.method_signature()

    @ABIReturnSubroutine
    def invalid_ret_type_collection(
        *, output: pt.abi.Tuple2[pt.abi.Account, pt.abi.Uint64]
    ):
        return output.set(pt.abi.Account(), pt.abi.Uint64())

    with pytest.raises(pt.TealInputError):
        invalid_ret_type_collection.method_signature()

    @ABIReturnSubroutine
    def invalid_ret_type_collection_nested(
        *, output: pt.abi.DynamicArray[pt.abi.Tuple2[pt.abi.Account, pt.abi.Uint64]]
    ):
        return output.set(
            pt.abi.make(
                pt.abi.DynamicArray[pt.abi.Tuple2[pt.abi.Account, pt.abi.Uint64]]
            )
        )

    with pytest.raises(pt.TealInputError):
        invalid_ret_type_collection_nested.method_signature()


def test_subroutine_definition_validate():
    """
    DFS through SubroutineDefinition.validate()'s logic
    """

    def mock_subroutine_definition(implementation, has_abi_output=False):
        mock = pt.SubroutineDefinition(lambda: pt.Return(pt.Int(1)), pt.TealType.uint64)
        mock._validate()  # haven't failed with dummy implementation
        mock.implementation = implementation
        mock.has_abi_output = has_abi_output
        return mock

    not_callable = mock_subroutine_definition("I'm not callable")
    with pytest.raises(pt.TealInputError) as tie:
        not_callable._validate()

    assert tie.value == pt.TealInputError(
        "Input to SubroutineDefinition is not callable"
    )

    # input_types:

    three_params = mock_subroutine_definition(lambda x, y, z: pt.Return(pt.Int(1)))

    params, anns, arg_types, byrefs, abi_args, output_kwarg = three_params._validate()
    assert len(params) == 3
    assert anns == {}
    assert all(at is pt.Expr for at in arg_types)
    assert byrefs == set()
    assert abi_args == {}
    assert output_kwarg == {}

    def bad_return_impl() -> str:
        return pt.Return(pt.Int(1))  # type: ignore

    bad_return = mock_subroutine_definition(bad_return_impl)
    with pytest.raises(pt.TealInputError) as tie:
        bad_return._validate()

    assert tie.value == pt.TealInputError(
        "Function has return of disallowed type <class 'str'>. Only Expr is allowed"
    )

    # now we iterate through the implementation params validating each as we go

    def var_abi_output_impl(*, output: pt.abi.Uint16):
        pt.Return(pt.Int(1))  # this is wrong but ignored

    # raises without abi_output_arg_name:
    var_abi_output_noname = mock_subroutine_definition(var_abi_output_impl)
    with pytest.raises(pt.TealInputError) as tie:
        var_abi_output_noname._validate()

    assert tie.value == pt.TealInputError(
        "Function has a parameter type that is not allowed in a subroutine: parameter output with type KEYWORD_ONLY"
    )

    # copacetic abi output:
    var_abi_output = mock_subroutine_definition(
        var_abi_output_impl, has_abi_output=True
    )
    params, anns, arg_types, byrefs, abi_args, output_kwarg = var_abi_output._validate()
    assert len(params) == 1
    assert anns == {"output": pt.abi.Uint16}
    assert all(at is pt.Expr for at in arg_types)
    assert byrefs == set()
    assert abi_args == {}
    assert output_kwarg == {"output": pt.abi.Uint16TypeSpec()}

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

    # Now we get to _validate_annotation():
    one_vanilla = mock_subroutine_definition(lambda _: pt.Return(pt.Int(1)))

    params, anns, arg_types, byrefs, abi_args, output_kwarg = one_vanilla._validate()
    assert len(params) == 1
    assert anns == {}
    assert all(at is pt.Expr for at in arg_types)
    assert byrefs == set()
    assert abi_args == {}
    assert output_kwarg == {}

    def one_expr_impl(x: pt.Expr):
        return pt.Return(pt.Int(1))

    one_expr = mock_subroutine_definition(one_expr_impl)
    params, anns, arg_types, byrefs, abi_args, output_kwarg = one_expr._validate()
    assert len(params) == 1
    assert anns == {"x": pt.Expr}
    assert all(at is pt.Expr for at in arg_types)
    assert byrefs == set()
    assert abi_args == {}
    assert output_kwarg == {}

    def one_scratchvar_impl(x: pt.ScratchVar):
        return pt.Return(pt.Int(1))

    one_scratchvar = mock_subroutine_definition(one_scratchvar_impl)
    params, anns, arg_types, byrefs, abi_args, output_kwarg = one_scratchvar._validate()
    assert len(params) == 1
    assert anns == {"x": pt.ScratchVar}
    assert all(at is pt.ScratchVar for at in arg_types)
    assert byrefs == {"x"}
    assert abi_args == {}
    assert output_kwarg == {}

    # not is_class()
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
        "Function has parameter x of disallowed type <class 'pyteal.DynamicScratchVar'>. Only the types (<class 'pyteal.Expr'>, <class 'pyteal.ScratchVar'>, 'ABI') are allowed"
    )

    # Now we're back to _validate() main body and looking at input_types

    three_params_with_output = mock_subroutine_definition(
        lambda x, y, z, *, output: pt.Return(pt.Int(1)), has_abi_output=True
    )
    four_inputs = [
        pt.TealType.uint64,
        pt.TealType.uint64,
        pt.TealType.bytes,
        pt.TealType.uint64,
    ]

    two_inputs = [pt.TealType.uint64, pt.TealType.bytes]
    with pytest.raises(pt.TealInputError) as tie:
        three_params._validate(input_types=two_inputs)

    assert tie.value == pt.TealInputError(
        "Provided number of input_types (2) does not match detected number of input parameters (3)"
    )

    three_inputs_with_a_wrong_type = [pt.TealType.uint64, pt.Expr, pt.TealType.bytes]

    with pytest.raises(pt.TealInputError) as tie:
        three_params._validate(input_types=three_inputs_with_a_wrong_type)

    assert tie.value == pt.TealInputError(
        "Function has input type <class 'pyteal.Expr'> for parameter y which is not a TealType"
    )

    with pytest.raises(pt.TealInputError) as tie:
        three_params._validate(
            input_types=[pt.TealType.uint64, pt.Expr, pt.TealType.anytype]
        )

    assert tie.value == pt.TealInputError(
        "Function has input type <class 'pyteal.Expr'> for parameter y which is not a TealType"
    )

    with pytest.raises(pt.TealInputError) as tie:
        three_params._validate(
            input_types=[pt.TealType.uint64, None, pt.TealType.anytype]
        )
    assert tie.value == pt.TealInputError(
        "input_type for y is unspecified i.e. None but this is only allowed for ABI arguments"
    )

    # this one gets caught inside of _validate_annotation()
    with pytest.raises(pt.TealInputError) as tie:
        three_params_with_output._validate(input_types=four_inputs)

    # everything should be copacetic
    for x, y, z in product(pt.TealType, pt.TealType, pt.TealType):
        (
            params,
            anns,
            arg_types,
            byrefs,
            abi_args,
            output_kwarg,
        ) = three_params._validate(input_types=[x, y, z])
        assert len(params) == 3
        assert anns == {}
        assert all(at is pt.Expr for at in arg_types)
        assert byrefs == set()
        assert abi_args == {}
        assert output_kwarg == {}

    # annotation / abi type handling:
    abi_annotation_examples = {
        pt.abi.Address: pt.abi.AddressTypeSpec(),
        pt.abi.Bool: pt.abi.BoolTypeSpec(),
        pt.abi.Byte: pt.abi.ByteTypeSpec(),
        pt.abi.DynamicArray[pt.abi.Bool]: pt.abi.DynamicArrayTypeSpec(
            pt.abi.BoolTypeSpec()
        ),
        pt.abi.StaticArray[pt.abi.Uint32, Literal[10]]: pt.abi.StaticArrayTypeSpec(
            pt.abi.Uint32TypeSpec(), 10
        ),
        pt.abi.String: pt.abi.StringTypeSpec(),
        pt.abi.Tuple2[pt.abi.Bool, pt.abi.Uint32]: pt.abi.TupleTypeSpec(
            pt.abi.BoolTypeSpec(), pt.abi.Uint32TypeSpec()
        ),
        pt.abi.Uint8: pt.abi.Uint8TypeSpec(),
        pt.abi.Uint16: pt.abi.Uint16TypeSpec(),
        pt.abi.Uint32: pt.abi.Uint32TypeSpec(),
        pt.abi.Uint64: pt.abi.Uint64TypeSpec(),
    }

    anns = (pt.Expr, pt.ScratchVar) + tuple(abi_annotation_examples.keys())
    for x_ann, z_ann in product(anns, anns):

        def mocker_impl(x: x_ann, y, z: z_ann):
            return pt.Return(pt.Int(1))

        mocker = mock_subroutine_definition(mocker_impl)
        params, anns, arg_types, byrefs, abis, output_kwarg = mocker._validate()
        print(
            f"{x_ann=}, {z_ann=}, {params=}, {anns=}, {arg_types=}, {byrefs=}, {abis=}, {output_kwarg=}"
        )

        assert len(params) == 3

        assert anns == {"x": x_ann, "z": z_ann}

        assert (
            (arg_types[0] is x_ann or arg_types[0] == abi_annotation_examples[x_ann])
            and arg_types[1] is pt.Expr
            and (
                arg_types[2] is z_ann or arg_types[2] == abi_annotation_examples[z_ann]
            )
        ), f"{arg_types[0]} -> {x_ann} and {arg_types[1]} -> {pt.Expr} and {arg_types[2]} -> {z_ann}"

        assert byrefs == set(["x"] if x_ann is pt.ScratchVar else []) | set(
            ["z"] if z_ann is pt.ScratchVar else []
        )
        expected_abis = {}
        if x_ann not in (pt.Expr, pt.ScratchVar):
            expected_abis["x"] = abi_annotation_examples[x_ann]
        if z_ann not in (pt.Expr, pt.ScratchVar):
            expected_abis["z"] = abi_annotation_examples[z_ann]
        assert abis == expected_abis


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
    av_bool_dym_arr = pt.abi.DynamicArray(
        pt.abi.DynamicArrayTypeSpec(pt.abi.BoolTypeSpec())
    )
    av_u32_static_arr = pt.abi.StaticArray(
        pt.abi.StaticArrayTypeSpec(pt.abi.Uint32TypeSpec(), 10)
    )
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
        assert definition.argument_count() == len(args), case_name
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


def test_abi_subroutine_calling_param_types():
    @pt.ABIReturnSubroutine
    def fn_log_add(a: pt.abi.Uint64, b: pt.abi.Uint32) -> pt.Expr:
        return pt.Seq(pt.Log(pt.Itob(a.get() + b.get())), pt.Return())

    @pt.ABIReturnSubroutine
    def fn_ret_add(
        a: pt.abi.Uint64, b: pt.abi.Uint32, *, output: pt.abi.Uint64
    ) -> pt.Expr:
        return output.set(a.get() + b.get() + pt.Int(0xA190))

    @pt.ABIReturnSubroutine
    def fn_abi_annotations_0(
        a: pt.abi.Byte,
        b: pt.abi.StaticArray[pt.abi.Uint32, Literal[10]],
        c: pt.abi.DynamicArray[pt.abi.Bool],
    ) -> pt.Expr:
        return pt.Return()

    @pt.ABIReturnSubroutine
    def fn_abi_annotations_0_with_ret(
        a: pt.abi.Byte,
        b: pt.abi.StaticArray[pt.abi.Uint32, Literal[10]],
        c: pt.abi.DynamicArray[pt.abi.Bool],
        *,
        output: pt.abi.Byte,
    ):
        return output.set(a)

    @pt.ABIReturnSubroutine
    def fn_mixed_annotations_0(a: pt.ScratchVar, b: pt.Expr, c: pt.abi.Byte) -> pt.Expr:
        return pt.Seq(
            a.store(c.get() * pt.Int(0x0FF1CE) * b),
            pt.Return(),
        )

    @pt.ABIReturnSubroutine
    def fn_mixed_annotations_0_with_ret(
        a: pt.ScratchVar, b: pt.Expr, c: pt.abi.Byte, *, output: pt.abi.Uint64
    ) -> pt.Expr:
        return pt.Seq(
            a.store(c.get() * pt.Int(0x0FF1CE) * b),
            output.set(a.load()),
        )

    @pt.ABIReturnSubroutine
    def fn_mixed_annotation_1(
        a: pt.ScratchVar, b: pt.abi.StaticArray[pt.abi.Uint32, Literal[10]]
    ) -> pt.Expr:
        return pt.Seq(
            (intermediate := pt.abi.Uint32()).set(b[a.load() % pt.Int(10)]),
            a.store(intermediate.get()),
            pt.Return(),
        )

    @pt.ABIReturnSubroutine
    def fn_mixed_annotation_1_with_ret(
        a: pt.ScratchVar, b: pt.abi.Uint64, *, output: pt.abi.Bool
    ) -> pt.Expr:
        return output.set((a.load() + b.get()) % pt.Int(2))

    abi_u64 = pt.abi.Uint64()
    abi_u32 = pt.abi.Uint32()
    abi_byte = pt.abi.Byte()
    abi_static_u32_10 = pt.abi.StaticArray(
        pt.abi.StaticArrayTypeSpec(pt.abi.Uint32TypeSpec(), 10)
    )
    abi_dynamic_bool = pt.abi.DynamicArray(
        pt.abi.DynamicArrayTypeSpec(pt.abi.BoolTypeSpec())
    )
    sv = pt.ScratchVar()
    expr_int = pt.Int(1)

    cases = [
        ("vanilla 1", fn_log_add, [abi_u64, abi_u32], "void", None),
        (
            "vanilla 1 with wrong ABI type",
            fn_log_add,
            [abi_u64, abi_u64],
            None,
            pt.TealInputError,
        ),
        (
            "vanilla 1 with ABI return",
            fn_ret_add,
            [abi_u64, abi_u32],
            pt.abi.Uint64TypeSpec(),
            None,
        ),
        (
            "vanilla 1 with ABI return wrong typed",
            fn_ret_add,
            [abi_u32, abi_u64],
            None,
            pt.TealInputError,
        ),
        (
            "full ABI annotations no return",
            fn_abi_annotations_0,
            [abi_byte, abi_static_u32_10, abi_dynamic_bool],
            "void",
            None,
        ),
        (
            "full ABI annotations wrong input 0",
            fn_abi_annotations_0,
            [abi_u64, abi_static_u32_10, abi_dynamic_bool],
            None,
            pt.TealInputError,
        ),
        (
            "full ABI annotations with ABI return",
            fn_abi_annotations_0_with_ret,
            [abi_byte, abi_static_u32_10, abi_dynamic_bool],
            pt.abi.ByteTypeSpec(),
            None,
        ),
        (
            "full ABI annotations with ABI return wrong inputs",
            fn_abi_annotations_0_with_ret,
            [abi_byte, abi_dynamic_bool, abi_static_u32_10],
            None,
            pt.TealInputError,
        ),
        (
            "mixed with ABI annotations 0",
            fn_mixed_annotations_0,
            [sv, expr_int, abi_byte],
            "void",
            None,
        ),
        (
            "mixed with ABI annotations 0 wrong inputs",
            fn_mixed_annotations_0,
            [abi_u64, expr_int, abi_byte],
            None,
            pt.TealInputError,
        ),
        (
            "mixed with ABI annotations 0 with ABI return",
            fn_mixed_annotations_0_with_ret,
            [sv, expr_int, abi_byte],
            pt.abi.Uint64TypeSpec(),
            None,
        ),
        (
            "mixed with ABI annotations 0 with ABI return wrong inputs",
            fn_mixed_annotations_0_with_ret,
            [sv, expr_int, sv],
            None,
            pt.TealInputError,
        ),
        (
            "mixed with ABI annotations 1",
            fn_mixed_annotation_1,
            [sv, abi_static_u32_10],
            "void",
            None,
        ),
        (
            "mixed with ABI annotations 1 with ABI return",
            fn_mixed_annotation_1_with_ret,
            [sv, abi_u64],
            pt.abi.BoolTypeSpec(),
            None,
        ),
        (
            "mixed with ABI annotations 1 with ABI return wrong inputs",
            fn_mixed_annotation_1_with_ret,
            [expr_int, abi_static_u32_10],
            None,
            pt.TealInputError,
        ),
    ]

    for case_name, definition, args, ret_type, err in cases:
        assert definition.subroutine.argument_count() == len(args), case_name
        assert (
            definition.name() == definition.subroutine.implementation.__name__
        ), case_name

        if err is None:
            invocation = definition(*args)
            if ret_type == "void":
                assert isinstance(invocation, pt.SubroutineCall), case_name
                assert not invocation.has_return(), case_name
                assert invocation.args == args, case_name
            else:
                assert isinstance(invocation, pt.abi.ReturnedValue), case_name
                assert invocation.type_spec == ret_type
                assert isinstance(invocation.computation, pt.SubroutineCall), case_name
                assert not invocation.computation.has_return(), case_name
                assert invocation.computation.args == args, case_name
        else:
            try:
                with pytest.raises(err):
                    definition(*args)
            except Exception as e:
                assert (
                    not e
                ), f"EXPECTED ERROR of type {err}. encountered unexpected error during invocation case <{case_name}>: {e}"


def test_subroutine_definition_invalid():
    def fnWithDefaults(a, b=None):
        return pt.Return()

    def fnWithKeywordArgs(a, *, output):
        return pt.Return()

    def fnWithKeywordArgsWrongKWName(a, *, b: pt.abi.Uint64):
        return pt.Return()

    def fnWithMultipleABIKeywordArgs(a, *, b: pt.abi.Byte, c: pt.abi.Bool):
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
        return pt.abi.StaticArray(
            pt.abi.StaticArrayTypeSpec(pt.abi.Uint32TypeSpec(), 10)
        )

    def fnWithMixedAnnsABIRet2(
        a: pt.Expr, b: pt.abi.Byte, c: pt.ScratchVar
    ) -> pt.abi.Uint64:
        return pt.abi.Uint64()

    cases = (
        (
            1,
            "TealInputError('Input to SubroutineDefinition is not callable'",
            "TealInputError('Input to ABIReturnSubroutine is not callable'",
        ),
        (
            None,
            "TealInputError('Input to SubroutineDefinition is not callable'",
            "TealInputError('Input to ABIReturnSubroutine is not callable'",
        ),
        (
            fnWithDefaults,
            "TealInputError('Function has a parameter with a default value, which is not allowed in a subroutine: b'",
            "TealInputError('Function has a parameter with a default value, which is not allowed in a subroutine: b'",
        ),
        (
            fnWithKeywordArgs,
            "TealInputError('Function has a parameter type that is not allowed in a subroutine: parameter output with type",
            "TealInputError('ABI return subroutine output-kwarg output must specify ABI type')",
        ),
        (
            fnWithKeywordArgsWrongKWName,
            "TealInputError('Function has a parameter type that is not allowed in a subroutine: parameter b with type",
            "TealInputError('ABI return subroutine output-kwarg name must be `output` at this moment",
        ),
        (
            fnWithMultipleABIKeywordArgs,
            "TealInputError('Function has a parameter type that is not allowed in a subroutine: parameter b with type",
            "multiple output arguments (2) with type annotations",
        ),
        (
            fnWithVariableArgs,
            "TealInputError('Function has a parameter type that is not allowed in a subroutine: parameter b with type",
            "Function has a parameter type that is not allowed in a subroutine: parameter b with type VAR_POSITIONAL",
        ),
        (
            fnWithNonExprReturnAnnotation,
            "Function has return of disallowed type TealType.uint64. Only Expr is allowed",
            "Function has return of disallowed type TealType.uint64. Only Expr is allowed",
        ),
        (
            fnWithNonExprParamAnnotation,
            "Function has parameter b of declared type TealType.uint64 which is not a class",
            "Function has parameter b of declared type TealType.uint64 which is not a class",
        ),
        (
            fnWithScratchVarSubclass,
            "Function has parameter b of disallowed type <class 'pyteal.DynamicScratchVar'>",
            "Function has parameter b of disallowed type <class 'pyteal.DynamicScratchVar'>",
        ),
        (
            fnReturningExprSubclass,
            "Function has return of disallowed type <class 'pyteal.Return'>",
            "Function has return of disallowed type <class 'pyteal.Return'>. Only Expr is allowed",
        ),
        (
            fnWithMixedAnns4AndBytesReturn,
            "Function has return of disallowed type <class 'pyteal.Bytes'>",
            "Function has return of disallowed type <class 'pyteal.Bytes'>. Only Expr is allowed",
        ),
        (
            fnWithMixedAnnsABIRet1,
            "Function has return of disallowed type pyteal.abi.StaticArray[pyteal.abi.Uint32, typing.Literal[10]]. "
            "Only Expr is allowed",
            "Function has return of disallowed type pyteal.abi.StaticArray[pyteal.abi.Uint32, typing.Literal[10]]. "
            "Only Expr is allowed",
        ),
        (
            fnWithMixedAnnsABIRet2,
            "Function has return of disallowed type <class 'pyteal.abi.Uint64'>. Only Expr is allowed",
            "Function has return of disallowed type <class 'pyteal.abi.Uint64'>. Only Expr is allowed",
        ),
    )

    for fn, sub_def_msg, abi_sub_def_msg in cases:
        with pytest.raises(pt.TealInputError) as e:
            print(f"case=[{sub_def_msg}]")
            pt.SubroutineDefinition(fn, pt.TealType.none)

        assert sub_def_msg in str(e), f"failed for case [{fn.__name__}]"

        with pytest.raises(pt.TealInputError) as e:
            print(f"case=[{abi_sub_def_msg}]")
            pt.ABIReturnSubroutine(fn)

        assert abi_sub_def_msg in str(e), f"failed for case[{fn.__name__}]"


def test_subroutine_declaration():
    cases = (
        (pt.TealType.none, pt.Return()),
        (pt.TealType.uint64, pt.Return(pt.Int(1))),
        (pt.TealType.uint64, pt.Int(1)),
        (pt.TealType.bytes, pt.Bytes("value")),
        (pt.TealType.anytype, pt.App.globalGet(pt.Bytes("key"))),
    )

    for returnType, value in cases:

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


SUBROUTINE_VAR_ARGS_CASES = [
    (pt.TealType.none, pt.Return()),
    (pt.TealType.uint64, pt.Int(1) + pt.Int(2)),
    (pt.TealType.uint64, pt.Return(pt.Int(1) + pt.Int(2))),
    (pt.TealType.bytes, pt.Bytes("value")),
    (pt.TealType.bytes, pt.Return(pt.Bytes("value"))),
]


@pytest.mark.parametrize("return_type, return_value", SUBROUTINE_VAR_ARGS_CASES)
def test_evaluate_subroutine_no_args(return_type: pt.TealType, return_value: pt.Expr):
    def mySubroutine():
        return return_value

    definition = pt.SubroutineDefinition(mySubroutine, return_type)
    evaluate_subroutine = SubroutineEval.normal_evaluator()

    declaration = evaluate_subroutine.evaluate(definition)

    assert isinstance(declaration, pt.SubroutineDeclaration)
    assert declaration.subroutine is definition

    assert declaration.type_of() == return_value.type_of()
    assert declaration.has_return() == return_value.has_return()

    options.setSubroutine(definition)
    expected, _ = pt.Seq([return_value]).__teal__(options)

    actual, _ = declaration.__teal__(options)
    options.setSubroutine(None)
    assert actual == expected


@pytest.mark.parametrize("return_type, return_value", SUBROUTINE_VAR_ARGS_CASES)
def test_evaluate_subroutine_1_arg(return_type: pt.TealType, return_value: pt.Expr):
    argSlots: list[pt.ScratchSlot] = []

    def mySubroutine(a1):
        assert isinstance(a1, pt.ScratchLoad)
        argSlots.append(a1.slot)
        return return_value

    definition = pt.SubroutineDefinition(mySubroutine, return_type)

    evaluate_subroutine = SubroutineEval.normal_evaluator()
    declaration = evaluate_subroutine.evaluate(definition)

    assert isinstance(declaration, pt.SubroutineDeclaration)
    assert declaration.subroutine is definition

    assert declaration.type_of() == return_value.type_of()
    assert declaration.has_return() == return_value.has_return()

    assert isinstance(declaration.body, pt.Seq)
    assert len(declaration.body.args) == 2

    assert isinstance(declaration.body.args[0], pt.ScratchStackStore)

    assert declaration.body.args[0].slot is argSlots[-1]

    options.setSubroutine(definition)
    expected, _ = pt.Seq([declaration.body.args[0], return_value]).__teal__(options)

    actual, _ = declaration.__teal__(options)
    options.setSubroutine(None)
    assert actual == expected


@pytest.mark.parametrize("return_type, return_value", SUBROUTINE_VAR_ARGS_CASES)
def test_evaluate_subroutine_2_args(return_type: pt.TealType, return_value: pt.Expr):
    argSlots: list[pt.ScratchSlot] = []

    def mySubroutine(a1, a2):
        assert isinstance(a1, pt.ScratchLoad)
        argSlots.append(a1.slot)
        assert isinstance(a2, pt.ScratchLoad)
        argSlots.append(a2.slot)
        return return_value

    definition = pt.SubroutineDefinition(mySubroutine, return_type)

    evaluate_subroutine = SubroutineEval.normal_evaluator()
    declaration = evaluate_subroutine.evaluate(definition)

    assert isinstance(declaration, pt.SubroutineDeclaration)
    assert declaration.subroutine is definition

    assert declaration.type_of() == return_value.type_of()
    assert declaration.has_return() == return_value.has_return()

    assert isinstance(declaration.body, pt.Seq)
    assert len(declaration.body.args) == 3

    assert isinstance(declaration.body.args[0], pt.ScratchStackStore)
    assert isinstance(declaration.body.args[1], pt.ScratchStackStore)

    assert declaration.body.args[0].slot is argSlots[-1]
    assert declaration.body.args[1].slot is argSlots[-2]

    options.setSubroutine(definition)
    expected, _ = pt.Seq(
        [declaration.body.args[0], declaration.body.args[1], return_value]
    ).__teal__(options)

    actual, _ = declaration.__teal__(options)
    options.setSubroutine(None)
    assert actual == expected


@pytest.mark.parametrize("return_type, return_value", SUBROUTINE_VAR_ARGS_CASES)
def test_evaluate_subroutine_10_args(return_type: pt.TealType, return_value: pt.Expr):
    argSlots: list[pt.ScratchSlot] = []

    def mySubroutine(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
        for a in (a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
            assert isinstance(a, pt.ScratchLoad)
            argSlots.append(a.slot)
        return return_value

    definition = pt.SubroutineDefinition(mySubroutine, return_type)

    evaluate_subroutine = SubroutineEval.normal_evaluator()
    declaration = evaluate_subroutine.evaluate(definition)

    assert isinstance(declaration, pt.SubroutineDeclaration)
    assert declaration.subroutine is definition

    assert declaration.type_of() == return_value.type_of()
    assert declaration.has_return() == return_value.has_return()

    assert isinstance(declaration.body, pt.Seq)
    assert len(declaration.body.args) == 11

    for i in range(10):
        assert isinstance(declaration.body.args[i], pt.ScratchStackStore)

    for i in range(10):
        assert declaration.body.args[i].slot is argSlots[-i - 1]

    options.setSubroutine(definition)
    expected, _ = pt.Seq(declaration.body.args[:10] + [return_value]).__teal__(options)

    actual, _ = declaration.__teal__(options)
    options.setSubroutine(None)
    assert actual == expected


@pytest.mark.parametrize("return_type, return_value", SUBROUTINE_VAR_ARGS_CASES)
def test_evaluate_subroutine_frame_pt_version(
    return_type: pt.TealType, return_value: pt.Expr
):
    def mySubroutine_no_arg():
        return return_value

    def mySubroutine_arg_1(a1):
        return return_value

    def mySubroutine_arg_2(a1, a2):
        return return_value

    def mySubroutine_arg_10(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
        return return_value

    for subr in [
        mySubroutine_no_arg,
        mySubroutine_arg_1,
        mySubroutine_arg_2,
        mySubroutine_arg_10,
    ]:
        subr = cast(Callable[..., pt.Expr], subr)
        definition = pt.SubroutineDefinition(subr, return_type)
        evaluate_subroutine = SubroutineEval.fp_evaluator()

        declaration = evaluate_subroutine.evaluate(definition)

        assert isinstance(declaration, pt.SubroutineDeclaration)
        assert declaration.subroutine is definition

        assert declaration.type_of() == return_value.type_of()
        assert declaration.has_return() == return_value.has_return()

        assert isinstance(declaration.body, pt.Seq)
        assert len(declaration.body.args) == 2

        assert isinstance(declaration.body.args[0], Proto)

        proto_expr = declaration.body.args[0]
        assert proto_expr.num_returns == int(return_type != pt.TealType.none)
        assert proto_expr.num_args == len(signature(subr).parameters)

        assert isinstance(declaration.body.args[1], type(return_value))

        options_v8.setSubroutine(definition)
        expected, _ = pt.Seq([declaration.body.args[0], return_value]).__teal__(
            options_v8
        )

        actual, _ = declaration.__teal__(options_v8)
        options_v8.setSubroutine(None)
        assert actual == expected


@dataclass
class LocalVariableTestCase:
    input_subroutine: Callable[..., pt.Expr]
    input_subroutine_return_type: pt.TealType
    input_subroutine_abi_return: bool
    expected_body_normal_evaluator: pt.Expr
    expected_body_fp_evaluator: pt.Expr


def example_subroutine_no_args_no_return():
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
    )


def example_subroutine_no_args_uint64_return():
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        local_scratch_var.store(pt.Int(1)), local_abi_type.set(pt.Int(2)), pt.Int(3)
    )


def example_subroutine_no_args_bytes_return():
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
        pt.Bytes(b"abc"),
    )


def example_subroutine_no_args_abi_return(*, output: pt.abi.Uint64):
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
        output.set(pt.Int(3)),
    )


def example_subroutine_expr_args_uint64_return(a: pt.Expr, b: pt.Expr):
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        pt.Pop(a == pt.Len(b)),
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
        pt.Int(3),
    )


def example_subroutine_expr_args_bytes_return(a: pt.Expr, b: pt.Expr):
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        pt.Pop(a == pt.Len(b)),
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
        pt.Bytes(b"abc"),
    )


def example_subroutine_expr_args_abi_return(
    a: pt.Expr, b: pt.Expr, *, output: pt.abi.StaticBytes[Literal[5]]
):
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        pt.Pop(a == pt.Len(b)),
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
        output.set(b"hello"),
    )


def example_subroutine_abi_args_uint64_return(a: pt.abi.Uint8, b: pt.abi.String):
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        pt.Pop(a.get() == pt.Len(b.get())),
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
        pt.Int(3),
    )


def example_subroutine_abi_args_bytes_return(a: pt.abi.Uint8, b: pt.abi.String):
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        pt.Pop(a.get() == pt.Len(b.get())),
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
        pt.Bytes(b"abc"),
    )


def example_subroutine_abi_args_abi_return(
    a: pt.abi.Uint8, b: pt.abi.String, *, output: pt.abi.StaticBytes[Literal[5]]
):
    local_scratch_var = pt.ScratchVar(pt.TealType.uint64)
    local_abi_type = pt.abi.Uint64()
    return pt.Seq(
        pt.Pop(a.get() == pt.Len(b.get())),
        local_scratch_var.store(pt.Int(1)),
        local_abi_type.set(pt.Int(2)),
        output.set(b"hello"),
    )


def example_subroutine_many_local_vars():
    local_abi_vars = [pt.abi.Uint64() for _ in range(200)]
    return pt.Seq([v.set(pt.Int(i)) for i, v in enumerate(local_abi_vars)])


@pytest.mark.parametrize(
    "test_case",
    [
        LocalVariableTestCase(
            input_subroutine=example_subroutine_no_args_no_return,
            input_subroutine_return_type=pt.TealType.none,
            input_subroutine_abi_return=False,
            expected_body_normal_evaluator=pt.Seq(
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    0,
                    0,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[],
                        local_stack_types=[pt.TealType.uint64],
                        num_return_allocs=0,
                    ),
                ),
                pt.ScratchVar().store(pt.Int(1)),
                FrameBury(pt.Int(2), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_no_args_uint64_return,
            input_subroutine_return_type=pt.TealType.uint64,
            input_subroutine_abi_return=False,
            expected_body_normal_evaluator=pt.Seq(
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                pt.Int(3),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    0,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[],
                        local_stack_types=[pt.TealType.uint64],
                        num_return_allocs=0,
                    ),
                ),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 0),
                # overwrite 1st local variable with the return value
                FrameBury(pt.Int(3), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_no_args_bytes_return,
            input_subroutine_return_type=pt.TealType.bytes,
            input_subroutine_abi_return=False,
            expected_body_normal_evaluator=pt.Seq(
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                pt.Bytes(b"abc"),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    0,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[],
                        local_stack_types=[pt.TealType.uint64],
                        num_return_allocs=0,
                    ),
                ),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 0),
                # overwrite 1st local variable with the return value
                FrameBury(pt.Bytes(b"abc"), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_no_args_abi_return,
            input_subroutine_return_type=pt.TealType.none,
            input_subroutine_abi_return=True,
            expected_body_normal_evaluator=pt.Seq(
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                (output_uint64 := pt.abi.Uint64()).set(pt.Int(3)),
                output_uint64.get(),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    0,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[],
                        local_stack_types=[pt.TealType.uint64, pt.TealType.uint64],
                        num_return_allocs=1,
                    ),
                ),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 1),
                FrameBury(pt.Int(3), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_expr_args_uint64_return,
            input_subroutine_return_type=pt.TealType.uint64,
            input_subroutine_abi_return=False,
            expected_body_normal_evaluator=pt.Seq(
                (arg2_expr := pt.ScratchVar()).slot.store(),
                (arg1_expr := pt.ScratchVar()).slot.store(),
                pt.Pop(arg1_expr.load() == pt.Len(arg2_expr.load())),
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                pt.Int(3),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    2,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[pt.TealType.anytype, pt.TealType.anytype],
                        local_stack_types=[pt.TealType.uint64],
                        num_return_allocs=0,
                    ),
                ),
                pt.Pop(FrameDig(-2) == pt.Len(FrameDig(-1))),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 0),
                # overwrite 1st local variable with the return value
                FrameBury(pt.Int(3), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_expr_args_bytes_return,
            input_subroutine_return_type=pt.TealType.bytes,
            input_subroutine_abi_return=False,
            expected_body_normal_evaluator=pt.Seq(
                (arg2_expr := pt.ScratchVar()).slot.store(),
                (arg1_expr := pt.ScratchVar()).slot.store(),
                pt.Pop(arg1_expr.load() == pt.Len(arg2_expr.load())),
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                pt.Bytes(b"abc"),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    2,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[pt.TealType.anytype, pt.TealType.anytype],
                        local_stack_types=[pt.TealType.uint64],
                        num_return_allocs=0,
                    ),
                ),
                pt.Pop(FrameDig(-2) == pt.Len(FrameDig(-1))),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 0),
                # overwrite 1st local variable with the return value
                FrameBury(pt.Bytes(b"abc"), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_expr_args_abi_return,
            input_subroutine_return_type=pt.TealType.none,
            input_subroutine_abi_return=True,
            expected_body_normal_evaluator=pt.Seq(
                (arg2_expr := pt.ScratchVar()).slot.store(),
                (arg1_expr := pt.ScratchVar()).slot.store(),
                pt.Pop(arg1_expr.load() == pt.Len(arg2_expr.load())),
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                (
                    output_static_bytes := pt.abi.make(pt.abi.StaticBytes[Literal[5]])
                ).set(b"hello"),
                output_static_bytes.get(),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    2,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[pt.TealType.anytype, pt.TealType.anytype],
                        local_stack_types=[pt.TealType.bytes, pt.TealType.uint64],
                        num_return_allocs=1,
                    ),
                ),
                pt.Pop(FrameDig(-2) == pt.Len(FrameDig(-1))),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 1),
                FrameBury(pt.Bytes(b"hello"), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_abi_args_uint64_return,
            input_subroutine_return_type=pt.TealType.uint64,
            input_subroutine_abi_return=False,
            expected_body_normal_evaluator=pt.Seq(
                cast(
                    pt.ScratchVar, (arg_string := pt.abi.String())._stored_value
                ).slot.store(),
                cast(
                    pt.ScratchVar, (arg_uint8 := pt.abi.Uint8())._stored_value
                ).slot.store(),
                pt.Pop(arg_uint8.get() == pt.Len(arg_string.get())),
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                pt.Int(3),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    2,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[pt.TealType.uint64, pt.TealType.bytes],
                        local_stack_types=[pt.TealType.uint64],
                        num_return_allocs=0,
                    ),
                ),
                pt.Pop(FrameDig(-2) == pt.Len(pt.Suffix(FrameDig(-1), pt.Int(2)))),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 0),
                # overwrite 1st local variable with the return value
                FrameBury(pt.Int(3), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_abi_args_bytes_return,
            input_subroutine_return_type=pt.TealType.bytes,
            input_subroutine_abi_return=False,
            expected_body_normal_evaluator=pt.Seq(
                cast(
                    pt.ScratchVar, (arg_string := pt.abi.String())._stored_value
                ).slot.store(),
                cast(
                    pt.ScratchVar, (arg_uint8 := pt.abi.Uint8())._stored_value
                ).slot.store(),
                pt.Pop(arg_uint8.get() == pt.Len(arg_string.get())),
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                pt.Bytes(b"abc"),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    2,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[pt.TealType.uint64, pt.TealType.bytes],
                        local_stack_types=[pt.TealType.uint64],
                        num_return_allocs=0,
                    ),
                ),
                pt.Pop(FrameDig(-2) == pt.Len(pt.Suffix(FrameDig(-1), pt.Int(2)))),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 0),
                # overwrite 1st local variable with the return value
                FrameBury(pt.Bytes(b"abc"), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_abi_args_abi_return,
            input_subroutine_return_type=pt.TealType.none,
            input_subroutine_abi_return=True,
            expected_body_normal_evaluator=pt.Seq(
                cast(
                    pt.ScratchVar, (arg_string := pt.abi.String())._stored_value
                ).slot.store(),
                cast(
                    pt.ScratchVar, (arg_uint8 := pt.abi.Uint8())._stored_value
                ).slot.store(),
                pt.Pop(arg_uint8.get() == pt.Len(arg_string.get())),
                pt.ScratchVar().store(pt.Int(1)),
                pt.abi.Uint64().set(pt.Int(2)),
                (
                    output_static_bytes := pt.abi.make(pt.abi.StaticBytes[Literal[5]])
                ).set(b"hello"),
                output_static_bytes.get(),
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    2,
                    1,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[pt.TealType.uint64, pt.TealType.bytes],
                        local_stack_types=[pt.TealType.bytes, pt.TealType.uint64],
                        num_return_allocs=1,
                    ),
                ),
                pt.Pop(FrameDig(-2) == pt.Len(pt.Suffix(FrameDig(-1), pt.Int(2)))),
                pt.ScratchVar(pt.TealType.uint64).store(pt.Int(1)),
                FrameBury(pt.Int(2), 1),
                FrameBury(pt.Bytes(b"hello"), 0),
            ),
        ),
        LocalVariableTestCase(
            input_subroutine=example_subroutine_many_local_vars,
            input_subroutine_return_type=pt.TealType.none,
            input_subroutine_abi_return=False,
            expected_body_normal_evaluator=pt.Seq(
                [pt.ScratchVar().store(pt.Int(i)) for i in range(200)]
            ),
            expected_body_fp_evaluator=pt.Seq(
                Proto(
                    0,
                    0,
                    mem_layout=ProtoStackLayout(
                        arg_stack_types=[],
                        local_stack_types=[pt.TealType.uint64] * 128,
                        num_return_allocs=0,
                    ),
                ),
                # 128 is the max number of frame pointer local+return vars
                *[FrameBury(pt.Int(i), i) for i in range(128)],
                *[pt.ScratchVar().store(pt.Int(i)) for i in range(128, 200)],
            ),
        ),
    ],
)
def test_evaluate_subroutine_local_variables(test_case: LocalVariableTestCase):
    definition = pt.SubroutineDefinition(
        test_case.input_subroutine,
        test_case.input_subroutine_return_type,
        has_abi_output=test_case.input_subroutine_abi_return,
    )

    for evaluator, expected_body in (
        (SubroutineEval.normal_evaluator(), test_case.expected_body_normal_evaluator),
        (SubroutineEval.fp_evaluator(), test_case.expected_body_fp_evaluator),
    ):
        declaration = evaluator.evaluate(definition)

        evaluator_type = "fp" if evaluator.use_frame_pt else "normal"
        failure_msg = f"assertion failed for {evaluator_type} evaluator"

        assert isinstance(declaration, pt.SubroutineDeclaration), failure_msg
        assert declaration.subroutine is definition, failure_msg

        assert (
            declaration.type_of() is test_case.input_subroutine_return_type
        ), failure_msg
        assert declaration.has_return() is False, failure_msg

        options_v8.setSubroutine(definition)

        expected, _ = expected_body.__teal__(options_v8)

        actual, actual_end = declaration.__teal__(options_v8)
        if declaration.deferred_expr is not None:
            # This is a hacky way to include the deferred expression in the resulting IR. It's only
            # valid if there are no retsub opcodes anywhere in the subroutine.

            for block in pt.TealBlock.Iterate(actual):
                assert all(
                    op.op != pt.Op.retsub for op in block.ops
                ), "retsub present in subroutine, test code to apply deferred expression is no longer valid"

            deferred, _ = declaration.deferred_expr.__teal__(options_v8)
            actual_end.setNextBlock(deferred)

        options_v8.setSubroutine(None)

        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality(), pt.TealComponent.Context.ignoreScratchSlotEquality():
            assert actual == expected, failure_msg

        assert pt.TealBlock.MatchScratchSlotReferences(
            pt.TealBlock.GetReferencedScratchSlots(actual),
            pt.TealBlock.GetReferencedScratchSlots(expected),
        ), failure_msg


def test_docstring_parsing_with_different_format():
    short_desc = "Example of a ABIReturnSubroutine with short description docstring."
    a_doc = "an abi Uint64 value"
    return_doc = "A PyTeal expression that sets output Uint64 value as argument a."
    long_desc = """Example first line.

    This is a second line.

    This is a third line that's so long it has to wrap in order to fit properly
    in a line of source code.
    """
    expected_long_desc = "Example first line.\nThis is a second line.\nThis is a third line that's so long it has to wrap in order to fit properly in a line of source code."

    def documented_method(a: pt.abi.Uint64, *, output: pt.abi.Uint64):
        return output.set(a)

    # Google format
    documented_method.__doc__ = f"""{short_desc}

    Args:
        a: {a_doc}

    Returns:
        {return_doc}
    """

    mspec_dict = pt.ABIReturnSubroutine(documented_method).method_spec().dictify()
    assert mspec_dict["desc"] == short_desc
    assert mspec_dict["args"][0]["desc"] == a_doc
    assert mspec_dict["returns"]["desc"] == return_doc

    # epy format
    documented_method.__doc__ = f"""
    {short_desc}

    @param a: {a_doc}
    @return: {return_doc}
    """

    mspec_dict = ABIReturnSubroutine(documented_method).method_spec().dictify()
    assert mspec_dict["desc"] == short_desc
    assert mspec_dict["args"][0]["desc"] == a_doc
    assert mspec_dict["returns"]["desc"] == return_doc

    # numpy format
    documented_method.__doc__ = f"""{short_desc}

    Parameters
    ----------
    a:
        an abi Uint64 value
    output:
        {a_doc}

    Returns
    -------
    uint64
        {return_doc}
    """

    mspec_dict = ABIReturnSubroutine(documented_method).method_spec().dictify()
    assert mspec_dict["desc"] == short_desc
    assert mspec_dict["args"][0]["desc"] == a_doc
    assert mspec_dict["returns"]["desc"] == return_doc

    # rst format
    documented_method.__doc__ = f"""{short_desc}

    :param a: {a_doc}
    :returns: {return_doc}
    """

    mspec_dict = ABIReturnSubroutine(documented_method).method_spec().dictify()
    assert mspec_dict["desc"] == short_desc
    assert mspec_dict["args"][0]["desc"] == a_doc
    assert mspec_dict["returns"]["desc"] == return_doc

    # Short and long descriptions
    documented_method.__doc__ = f"""{long_desc}

    :param a: {a_doc}
    :returns: {return_doc}
    """

    mspec_dict = ABIReturnSubroutine(documented_method).method_spec().dictify()
    assert mspec_dict["desc"] == expected_long_desc
    assert mspec_dict["args"][0]["desc"] == a_doc
    assert mspec_dict["returns"]["desc"] == return_doc

    # Only long description
    # Short description is defined as being on the first line, so by introducing
    # long_desc on the second, there is no short description.
    documented_method.__doc__ = f"""
    {long_desc}

    :param a: {a_doc}
    :returns: {return_doc}
    """

    mspec_dict = ABIReturnSubroutine(documented_method).method_spec().dictify()
    assert mspec_dict["desc"] == expected_long_desc
    assert mspec_dict["args"][0]["desc"] == a_doc
    assert mspec_dict["returns"]["desc"] == return_doc

    # No description
    documented_method.__doc__ = f"""

    :param a: {a_doc}
    :returns: {return_doc}
    """
    mspec_dict = ABIReturnSubroutine(documented_method).method_spec().dictify()
    assert "desc" not in mspec_dict
    assert mspec_dict["args"][0]["desc"] == a_doc
    assert mspec_dict["returns"]["desc"] == return_doc

    # No doc
    documented_method.__doc__ = None
    mspec_dict = ABIReturnSubroutine(documented_method).method_spec().dictify()
    assert "desc" not in mspec_dict
    assert len(mspec_dict["args"]) == 1

    algobank_example = """Withdraw an amount of Algos held by this app.

    The sender of this method call will be the source of the Algos, and the destination will be
    the `recipient` argument.

    The Algos will be transferred to the recipient using an inner transaction whose fee is set
    to 0, meaning the caller's transaction must include a surplus fee to cover the inner
    transaction.

    Args:
        amount: The amount of Algos requested to be withdraw, in microAlgos. This method will fail
            if this amount exceeds the amount of Algos held by this app for the method call sender.
        recipient: An account who will receive the withdrawn Algos. This may or may not be the same
            as the method call sender.
    """

    # algobank example
    def withdraw(amount: pt.abi.Uint64, recipient: pt.abi.Account):
        return pt.Assert(pt.Int(1))

    withdraw.__doc__ = algobank_example

    mspec_dict = ABIReturnSubroutine(withdraw).method_spec().dictify()
    assert (
        mspec_dict["desc"]
        == "Withdraw an amount of Algos held by this app.\nThe sender of this method call will be the source of the Algos, "
        + "and the destination will be the `recipient` argument.\nThe Algos will be transferred to the recipient using an inner transaction whose fee is "
        + "set to 0, meaning the caller's transaction must include a surplus fee to cover the inner transaction."
    )
    assert (
        mspec_dict["args"][0]["desc"]
        == "The amount of Algos requested to be withdraw, in microAlgos. This method will fail if this amount exceeds "
        + "the amount of Algos held by this app for the method call sender."
    )
    assert (
        mspec_dict["args"][1]["desc"]
        == "An account who will receive the withdrawn Algos. This may or may not be the same as the method call sender."
    )
    assert "desc" not in mspec_dict["returns"]


def test_relaxed_abi_arg():
    @pt.Subroutine(pt.TealType.none)
    def txn_checker(t: pt.abi.Transaction):
        return pt.Seq(
            pt.Assert(
                pt.Or(
                    t.get().type_enum() == pt.TxnType.Payment,
                    t.get().type_enum() == pt.TxnType.AssetTransfer,
                )
            )
        )

    # Pass a payment transaction to the subroutine that expects a Transaction type
    # this will fail if we don't have a relaxed type check for the transaction type
    program = pt.Seq(
        (p := pt.abi.PaymentTransaction())._set_index(pt.Txn.group_index() - pt.Int(1)),
        txn_checker(p),
        pt.Int(1),
    )

    pt.compileTeal(program, mode=pt.Mode.Application, version=7)


def test_override_abi_method_name():
    def abi_meth(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64):
        return output.set(a.get() + b.get())

    mspec = ABIReturnSubroutine(abi_meth).method_spec().dictify()
    assert mspec["name"] == "abi_meth"

    mspec = ABIReturnSubroutine(abi_meth, overriding_name="add").method_spec().dictify()
    assert mspec["name"] == "add"

    @ABIReturnSubroutine.name_override("overriden_add")
    def abi_meth_2(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64):
        return output.set(a.get() + b.get())

    mspec = abi_meth_2.method_spec().dictify()
    assert mspec["name"] == "overriden_add"


def test_frame_option_version_range_well_formed():
    assert (
        pt.Op.callsub.min_version < FRAME_POINTERS_VERSION < pt.MAX_PROGRAM_VERSION + 1
    )


def test_new_abi_instance_from_storage():
    current_proto = Proto(num_args=2, num_returns=1)

    current_scratch_slot_id = pt.ScratchSlot.nextSlotId

    arg_storage = FrameVar(current_proto, -1)
    some_arg_from_proto = SubroutineEval._new_abi_instance_from_storage(
        pt.abi.Uint64TypeSpec(),
        arg_storage,
    )

    assert some_arg_from_proto._stored_value == arg_storage
    assert current_scratch_slot_id == pt.ScratchSlot.nextSlotId

    ret_storage = FrameVar(current_proto, 0)
    ret_from_proto = SubroutineEval._new_abi_instance_from_storage(
        pt.abi.AddressTypeSpec(),
        ret_storage,
    )

    assert ret_from_proto._stored_value == ret_storage
    assert current_scratch_slot_id == pt.ScratchSlot.nextSlotId


def test_subroutine_evaluation_local_allocation_correct():
    foo = pt.abi.Uint64()

    @pt.ABIReturnSubroutine
    def get(
        x: pt.abi.Uint64, y: pt.abi.Uint8, *, output: pt.abi.DynamicBytes
    ) -> pt.Expr:
        return pt.Seq(
            output.set(pt.Bytes("")),
        )

    @pt.ABIReturnSubroutine
    def get_fie(y: pt.abi.Uint8, *, output: pt.abi.Uint64) -> pt.Expr:
        data = pt.abi.make(pt.abi.DynamicBytes)
        return pt.Seq(
            data.set(get(foo, y)),
            output.set(pt.Btoi(data.get())),
        )

    @pt.ABIReturnSubroutine
    def set_(x: pt.abi.Uint64, y: pt.abi.Uint8) -> pt.Expr:
        return pt.Seq()

    router = pt.Router("Jane Doe")

    @router.method
    def fie(y: pt.abi.Uint8) -> pt.Expr:
        old_amount = pt.abi.Uint64()

        return pt.Seq(
            old_amount.set(get_fie(y)),
            set_(foo, y),
        )

    evaluator = SubroutineEval.fp_evaluator()

    evaluated_fie = evaluator.evaluate(cast(pt.ABIReturnSubroutine, fie).subroutine)
    layout_fie = cast(Proto, cast(pt.Seq, evaluated_fie.body).args[0]).mem_layout

    assert len(layout_fie.local_stack_types) == 1

    evaluated_get_fie = evaluator.evaluate(
        cast(pt.ABIReturnSubroutine, get_fie).subroutine
    )
    layout_get_fie = cast(
        Proto, cast(pt.Seq, evaluated_get_fie.body).args[0]
    ).mem_layout

    assert len(layout_get_fie.local_stack_types) == 2
