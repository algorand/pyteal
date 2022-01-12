from typing import List, Tuple

from . import ScratchVar
from ..compiler import CompileOptions
from .binaryexpr import Op

from .abi_utils import accumulate, rest
from .abi_type import ABIType
from .abi_bytes import *
from .abi_uint import *


class ABITuple(ABIType):

    types: List[ABIType]
    value: Expr

    def __init__(self, t: List[ABIType]):
        self.stack_type = TealType.bytes
        self.types = t

    def __call__(self, *elements: ABIType) -> "ABITuple":
        """__call__ provides an method to construct a tuple for a list of types"""

        head_pos_lengths = []
        head_ops: List[Expr] = []
        tail_ops: List[Expr] = []
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

    def decode(self, value: Expr) -> "ABITuple":
        inst = ABITuple(self.types)
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
        return ("(" + ",".join(["{}"] * len(self.types)) + ")").format(
            *[t.__str__() for t in self.types]
        )

ABITuple.__module__ = "pyteal"

class ABIFixedArray(ABITuple):
    def __init__(self, t: ABIType, N: int):
        self.types = [t] * N

    def decode(self, value: Expr) -> "ABIFixedArray":
        inst = ABIFixedArray(self.types[0], len(self.types))
        inst.value = value
        return inst

    def __str__(self):
        return "{}[{}]".format(self.types[0].__str__(), len(self.types))

ABIFixedArray.__module__ = "pyteal"

class ABIDynamicArray(ABITuple):

    item_len: Uint16

    def __init__(self, type: ABIType):
        self.element_type = type

    def __call__(self, *data: ABIType) -> "ABIDynamicArray":
        return self.decode(
            Concat(Uint16(Int(len(data))).encode(), super().__call__(*data))
        )

    def decode(self, data: Expr) -> "ABIDynamicArray":
        da = ABIDynamicArray(self.element_type)
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
        return "{}[]".format(self.element_type.__str__())

ABIDynamicArray.__module__ = "pyteal"