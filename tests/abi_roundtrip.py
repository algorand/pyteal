from typing import Generic, TypeVar

import pyteal as pt
from pyteal import abi

from tests.blackbox import Blackbox, BlackboxWrapper, PyTealDryRunExecutor

T = TypeVar("T", bound=abi.BaseType)

DEFAULT_DYNAMIC_ARRAY_LENGTH = 3


class ABIRoundtrip(Generic[T]):
    def __init__(
        self,
        annotation_instance: abi.BaseType,
        length: int | None = None,
    ):
        self.instance: abi.BaseType = annotation_instance
        self.type_spec: abi.TypeSpec = annotation_instance.type_spec()
        self.annotation: type[abi.BaseType] = self.type_spec.annotation_type()

        self.length: int | None = length

    def pytealer(self) -> PyTealDryRunExecutor:
        roundtrip = self.roundtrip_factory()
        return PyTealDryRunExecutor(roundtrip, pt.Mode.Application)

    def roundtrip_factory(self) -> BlackboxWrapper:
        comp = self.mutator_factory()

        ann_out = abi.Tuple3[self.annotation, self.annotation, self.annotation]  # type: ignore[misc,name-defined]

        @Blackbox(input_types=[None])
        @pt.ABIReturnSubroutine
        def round_tripper(x: self.annotation, *, output: ann_out):  # type: ignore[name-defined]
            y = abi.make(self.annotation)
            z = abi.make(self.annotation)
            return pt.Seq(y.set(comp(x)), z.set(comp(y)), output.set(x, y, z))  # type: ignore[attr-defined]

        return round_tripper

    def mutator_factory(self) -> pt.ABIReturnSubroutine:
        if isinstance(self.type_spec, abi.BoolTypeSpec):
            return self.bool_comp_factory()
        if isinstance(self.type_spec, abi.UintTypeSpec):
            return self.numerical_comp_factory()
        if isinstance(self.type_spec, abi.StringTypeSpec):
            return self.string_reverse_factory()
        if isinstance(self.type_spec, abi.TupleTypeSpec):
            return self.tuple_comp_factory()
        if isinstance(self.type_spec, abi.ArrayTypeSpec):
            return self.array_comp_factory()
        if isinstance(self.type_spec, abi.TransactionTypeSpec):
            return self.transaction_comp_factory()

        raise ValueError(f"uh-oh!!! didn't handle type {self.instance}")

    def bool_comp_factory(self) -> pt.ABIReturnSubroutine:
        @pt.ABIReturnSubroutine
        def bool_comp(x: abi.Bool, *, output: abi.Bool):
            return output.set(pt.Not(x.get()))

        return bool_comp

    @classmethod
    def max_int(cls, bit_size):
        return (1 << bit_size) - 1

    def transaction_comp_factory(self) -> pt.ABIReturnSubroutine:
        @pt.ABIReturnSubroutine
        def transaction_comp(x: self.annotation, *, output: abi.Uint64):  # type: ignore[name-defined]
            return output.set(x.get().amount())

        return transaction_comp

    def numerical_comp_factory(self) -> pt.ABIReturnSubroutine:
        @pt.ABIReturnSubroutine
        def numerical_comp(x: self.annotation, *, output: self.annotation):  # type: ignore[name-defined]
            max_uint = pt.Int(self.max_int(self.type_spec.bit_size()))  # type: ignore[attr-defined]
            return output.set(max_uint - x.get())

        return numerical_comp

    def string_reverse_factory(self) -> pt.ABIReturnSubroutine:
        """
        Assume strings are python utf-8 compliant and therefore each byte value is at most 127
        """
        if self.length is None:
            self.length = DEFAULT_DYNAMIC_ARRAY_LENGTH

        char_type_spec = abi.ByteTypeSpec()

        @pt.ABIReturnSubroutine
        def string_reverse(x: self.annotation, *, output: self.annotation):  # type: ignore[name-defined]
            insts = [char_type_spec.new_instance() for _ in range(self.length)]  # type: ignore[arg-type]
            setters = [inst.set(x[i]) for i, inst in enumerate(reversed(insts))]
            return pt.Seq(*(setters + [output.set(insts)]))

        return string_reverse

    def tuple_comp_factory(self) -> pt.ABIReturnSubroutine:  # type: ignore[name-defined]
        value_type_specs: list[abi.TypeSpec] = self.type_spec.value_type_specs()  # type: ignore[attr-defined]
        insts = [vts.new_instance() for vts in value_type_specs]
        roundtrips: list[ABIRoundtrip[T]] = [
            ABIRoundtrip(inst, length=None) for inst in insts  # type: ignore[arg-type]
        ]

        @pt.ABIReturnSubroutine
        def tuple_complement(x: self.annotation, *, output: self.annotation):  # type: ignore[name-defined]
            setters = [inst.set(x[i]) for i, inst in enumerate(insts)]  # type: ignore[attr-defined]
            comp_funcs = [rtrip.mutator_factory() for rtrip in roundtrips]
            compers = [inst.set(comp_funcs[i](inst)) for i, inst in enumerate(insts)]  # type: ignore[attr-defined]
            return pt.Seq(*(setters + compers + [output.set(*insts)]))

        return tuple_complement

    def array_comp_factory(self) -> pt.ABIReturnSubroutine:
        """
        When the length has not been provided for a dynamic array,
        default to DEFAULT_DYNAMIC_ARRAY_LENGTH
        """
        if self.length is not None:
            assert self.type_spec.is_length_dynamic()  # type: ignore[attr-defined]
        elif not self.type_spec.is_length_dynamic():  # type: ignore[attr-defined]
            self.length = self.type_spec.length_static()  # type: ignore[attr-defined]
        else:
            self.length = DEFAULT_DYNAMIC_ARRAY_LENGTH

        internal_type_spec = self.type_spec.value_type_spec()  # type: ignore[attr-defined]
        internal_ann_inst = internal_type_spec.new_instance()
        comp_func = ABIRoundtrip(internal_ann_inst, length=None).mutator_factory()

        @pt.ABIReturnSubroutine
        def array_complement(x: self.annotation, *, output: self.annotation):  # type: ignore[name-defined]
            insts = [internal_type_spec.new_instance() for _ in range(self.length)]  # type: ignore[arg-type]
            setters = [inst.set(x[i]) for i, inst in enumerate(insts)]
            compers = [inst.set(comp_func(inst)) for inst in insts]
            return pt.Seq(*(setters + compers + [output.set(insts)]))

        return array_complement
