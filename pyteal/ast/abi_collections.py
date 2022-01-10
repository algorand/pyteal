from typing import List, Tuple

from . import ScratchVar
from .binaryexpr import Op

from .abi_utils import accumulate, rest
from .abi_type import ABIType
from .abi_bytes import *
from .abi_uint import *


class Tuple(ABIType):

    types: List[ABIType]
    value: Expr

    def __init__(self, t: List[ABIType]):
        self.stack_type = Bytes
        self.types = t

    def __call__(self, *elements: ABIType) -> "Tuple":
        """__call__ provides an method to construct a tuple for a list of types"""

        head_pos_lengths = []
        head_ops, tail_ops = [], []
        v, head_pos = ScratchVar(), ScratchVar()

        for elem in elements:
            if elem.dynamic:

                head_pos_lengths.append(elem.byte_len + Int(2))

                head_ops.append(
                    Seq(
                        # Move the header position back
                        head_pos.store(head_pos.load() - elem.byte_len),
                        # Write the pos bytes
                        v.store(Concat(Uint16(head_pos.load()).encode(), v.load())),
                    )
                )

                tail_ops.append(elem.encode())
            else:
                head_pos_lengths.append(elem.byte_len)
                head_ops.append(v.store(Concat(elem.encode(), v.load())))

        # Write them in reverse
        head_ops.reverse()

        return self.decode(
            Seq(
                v.store(Bytes("")),
                head_pos.store(accumulate(head_pos_lengths, Op.add)),
                *head_ops,
                Concat(v.load(), *tail_ops),
            )
        )

    def decode(self, value: Bytes) -> "Tuple":
        inst = Tuple(self.types)
        inst.value = value
        return inst

    def __getitem__(self, i: int) -> Expr:
        target_type = self.types[i]
        return target_type.decode(rest(self.value, self.element_position(i)))

    def element_position(self, i: int) -> Expr:
        pos = ScratchVar()
        ops = [pos.store(Int(0))]

        for t in self.types[:i]:
            if t.dynamic:
                # Just add uint16 length
                ops.append(pos.store(pos.load() + Int(2)))
            else:
                # Add length of static type
                ops.append(pos.store(pos.load() + t.byte_len))

        if self.types[i].dynamic:
            ops.append(pos.store(ExtractUint16(self.value, pos.load())))

        return Seq(*ops, pos.load())

    def encode(self) -> Expr:
        return self.value

    def __str__(self):
        return ("tuple(" + ",".join(["{}"] * len(self.types)) + ")").format(
            *[t.__name__.lower() for t in self.types]
        )


class FixedArray(Tuple):
    def __init__(self, t: ABIType, N: int):
        self.types = [t] * N

    def decode(self, value: Bytes) -> "FixedArray":
        inst = FixedArray(self.types[0], len(self.types))
        inst.value = value
        return inst

    def __str__(self):
        return "[{}]{}".format(len(self.types), self.types[0])


class DynamicArray(Tuple):

    item_len: Uint16

    def __init__(self, type: ABIType):
        self.element_type = type

    def __call__(self, data: List[ABIType]) -> "DynamicArray":
        return self.decode(
            Concat(Uint16(Int(len(data))).encode(), super().__call__(*data))
        )

    def decode(self, data: Bytes) -> "DynamicArray":
        da = DynamicArray(self.element_type)
        da.value = rest(data, Int(2))
        da.item_len = Uint16.decode(data)
        return da

    def element_position(self, i: int) -> Expr:
        pos = ScratchVar()
        ops = [pos.store(Int(0))]

        for t in self.types[:i]:
            if t.dynamic:
                # Just add uint16 length
                ops.append(pos.store(pos.load() + Int(2)))
            else:
                # Add length of static type
                ops.append(pos.store(pos.load() + t.byte_len))

        if self.types[i].dynamic:
            ops.append(pos.store(ExtractUint16(self.value, pos.load())))

        return Seq(*ops, pos.load())

    def __teal__(self, options: "CompileOptions"):
        return self.value.__teal__(options)

    def encode(self) -> Expr:
        return Concat(self.item_len.encode(), self.value)

    def __str__(self):
        return "[{}]{}".format(self.element_type)
