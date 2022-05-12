import pytest
from typing import Callable, Literal, TypeVar

import algosdk.abi

from pyteal import abi
import pyteal as pt

from tests.blackbox import Blackbox, PyTealDryRunExecutor

T = TypeVar("T", bound=abi.BaseType)


def max_int(bit_size):
    return (1 << bit_size) - 1


@pt.ABIReturnSubroutine
def bool_comp(x: abi.Bool, *, output: abi.Bool):
    return output.set(pt.Not(x.get()))


def numerical_comp_factory(t: type[T], bit_size: int) -> Callable:
    @pt.ABIReturnSubroutine
    def func(x: t, *, output: t):
        max_uint = pt.Int(max_int(bit_size))
        return output.set(max_uint - x.get())

    return func


def tuple_comp_factory(t: type[T], value_type_specs: list[abi.TypeSpec]) -> Callable:
    @pt.ABIReturnSubroutine
    def tuple_complement(x: t, *, output: t):
        value_types = [vts.new_instance() for vts in value_type_specs]
        setters = [vts.set(x[i]) for i, vts in enumerate(value_types)]
        comp_funcs = [complement_factory(type(vts), -1) for vts in value_types]
        compers = [vts.set(comp_funcs[i](vts)) for i, vts in enumerate(value_types)]
        return pt.Seq(*(setters + compers + [output.set(*value_types)]))

    return tuple_complement


def array_comp_factory(
    t: type[T], value_type_spec: abi.TypeSpec, length: int
) -> Callable:
    comp_func = complement_factory(type(value_type_spec.new_instance()), -1)
    if length != -1:
        assert t.type_spec().is_length_dynamic()
    else:
        length = t.length_static()

    @pt.ABIReturnSubroutine
    def array_complement(arr: t, *, output: t):
        i = pt.ScratchVar(pt.TealType.uint64)
        val = value_type_spec.new_instance()
        return pt.For(
            i.store(pt.Int(0)),
            i.load() < arr.length(),
            i.store(i.load() + pt.Int(1)),
        ).Do(
            pt.Seq(
                arr[i.load()].store_into(val),
                output.set()[i.load()].store_into(comp_func(val)),
            )
        )

    return array_complement


def complement_factory(t: T, dynamic_length: int) -> Callable:
    ts = abi.type_spec_from_annotation(t)
    if isinstance(ts, abi.BoolTypeSpec):
        return bool_comp
    if isinstance(ts, abi.UintTypeSpec):
        return numerical_comp_factory(t, ts.bit_size())
    if isinstance(ts, abi.TupleTypeSpec):
        return tuple_comp_factory(t, ts.value_type_specs())
    if isinstance(ts, abi.ArrayTypeSpec):
        return array_comp_factory(t, ts.value_type_spec(), dynamic_length)

    raise ValueError(f"uh-oh!!! didn't handle type {t}")


def roundtrip_factory(t: type[T], dynamic_length: int) -> Callable:
    comp = complement_factory(t, dynamic_length)

    @Blackbox(input_types=[None])
    @pt.ABIReturnSubroutine
    def round_tripper(x: t, *, output: abi.Tuple2[t, t]):
        y = abi.make(t)
        z = abi.make(t)
        return pt.Seq(y.set(comp(x)), z.set(comp(y)), output.set(y, z))

    return round_tripper


def roundtrip_pytealer(t: type[T]):
    roundtrip = roundtrip_factory(t)
    return PyTealDryRunExecutor(roundtrip, pt.Mode.Application)


ABI_TYPES = [
    abi.Bool,
    abi.Byte,
    abi.Uint8,
    abi.Uint16,
    abi.Uint32,
    abi.Uint64,
    abi.Tuple0,
    abi.Tuple1[abi.Bool],
    abi.Tuple1[abi.Byte],
    abi.Tuple1[abi.Uint8],
    abi.Tuple1[abi.Uint16],
    abi.Tuple1[abi.Uint32],
    abi.Tuple1[abi.Uint64],
    abi.Tuple3[abi.Bool, abi.Uint64, abi.Uint32],
    abi.Tuple3[abi.Byte, abi.Bool, abi.Uint64],
    abi.Tuple3[abi.Uint8, abi.Byte, abi.Bool],
    abi.Tuple3[abi.Uint16, abi.Uint8, abi.Byte],
    abi.Tuple3[abi.Uint32, abi.Uint16, abi.Uint8],
    abi.Tuple3[abi.Uint64, abi.Uint32, abi.Uint16],
    abi.StaticArray[abi.Bool, Literal[0]],
    abi.StaticArray[abi.Bool, Literal[42]],
    (abi.DynamicArray[abi.Bool], 0),
    (abi.DynamicArray[abi.Bool], 42),
]


@pytest.mark.skip("not ready")
@pytest.mark.parametrize("abi_type", ABI_TYPES)
def test_pure_compilation(abi_type):
    print(f"Testing {abi_type=}")
    dynamic_length = -1
    if isinstance(abi_type, tuple):
        abi_type, dynamic_length = abi_type

    sdk_abi_type = abi.algosdk_from_annotation(abi_type)

    roundtripper = roundtrip_pytealer(abi_type, dynamic_length)

    teal = roundtripper.program()

    abi_arg_types = roundtripper.abi_argument_types()
    assert [sdk_abi_type] == abi_arg_types

    abi_ret_type = roundtripper.abi_return_type()
    assert algosdk.abi.TupleType([sdk_abi_type] * 2) == abi_ret_type

    _ = teal
