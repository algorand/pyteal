import pytest
from typing import Callable, TypeVar

import algosdk.abi

from pyteal import abi
import pyteal as pt

from tests.blackbox import Blackbox, BlackboxPyTealer

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
        comp_funcs = [complement_factory(type(vts)) for vts in value_types]
        compers = [vts.set(comp_funcs[i](vts)) for i, vts in enumerate(value_types)]
        return pt.Seq(*(setters + compers + [output.set(*value_types)]))

    return tuple_complement


def complement_factory(t: T) -> Callable:
    ts = abi.type_spec_from_annotation(t)
    if isinstance(ts, abi.BoolTypeSpec):
        return bool_comp
    if isinstance(ts, abi.UintTypeSpec):
        return numerical_comp_factory(t, ts.bit_size())
    if isinstance(ts, abi.TupleTypeSpec):
        return tuple_comp_factory(t, ts.value_type_specs())

    raise ValueError(f"uh-oh!!! didn't handle type {t}")


def roundtrip_factory(t: type[T]) -> Callable:
    comp = complement_factory(t)

    @Blackbox(input_types=[None])
    @pt.ABIReturnSubroutine
    def round_tripper(x: t, *, output: abi.Tuple2[t, t]):
        y = abi.make(t)
        z = abi.make(t)
        return pt.Seq(y.set(comp(x)), z.set(comp(y)), output.set(y, z))

    return round_tripper


def roundtrip_pytealer(t: type[T]):
    roundtrip = roundtrip_factory(t)
    return BlackboxPyTealer(roundtrip, pt.Mode.Application)


ABI_TYPES = [
    abi.Bool,
    abi.Byte,
    abi.Uint8,
    abi.Uint16,
    abi.Uint32,
    abi.Uint64,
]


@pytest.mark.parametrize("abi_type", ABI_TYPES)
def test_pure_compilation(abi_type):
    print(f"Testing {abi_type=}")
    sdk_abi_type = abi.algosdk_from_annotation(abi_type)

    roundtripper = roundtrip_pytealer(abi_type)

    teal = roundtripper.program()

    abi_arg_types = roundtripper.abi_argument_types()
    assert [sdk_abi_type] == abi_arg_types

    abi_ret_type = roundtripper.abi_return_type()
    assert algosdk.abi.TupleType([sdk_abi_type] * 2) == abi_ret_type

    _ = teal
