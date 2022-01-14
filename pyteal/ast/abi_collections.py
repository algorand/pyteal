from typing import List, Generic, Sequence, TypeVar, get_type_hints

from . import ScratchVar
from ..compiler import CompileOptions
from .binaryexpr import Op

from .abi_utils import accumulate, rest
from .abi_type import ABIType
from .abi_bytes import *
from .abi_uint import *

T = TypeVar("T", bound=Sequence[ABIType])


class ABITuple(ABIType, Generic[T]):

    stack_type = TealType.bytes
    value: Expr
    types: T

    def __init__(self, data: Union[T, Expr]):

        # Yikes
        orig = getattr(self.__class__, "__orig_bases__")
        self.types = orig[0].__args__[0].__args__

        if isinstance(data, Expr):
            self.value = data
            return

        self.elements = data

        head_pos_lengths = []
        head_ops: List[Expr] = []
        tail_ops: List[Expr] = []
        v, head_pos = ScratchVar(), ScratchVar()

        for elem in data:
            elem = cast(ABIType, elem)
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

        self.value = Seq(
            v.store(Bytes("")),
            head_pos.store(accumulate(head_pos_lengths, Op.add)),
            *head_ops,
            Concat(v.load(), *tail_ops),
        )

    @classmethod
    def decode(cls, value: Expr) -> "ABITuple[T]":
        return cls(value)

    def __len__(self) -> int:
        return len(self.elements)

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

    @classmethod
    def __str__(cls):
        types = cls.__orig_bases__[0].__args__[0].__args__
        return ("(" + ",".join(["{}"] * len(types)) + ")").format(
            *[t.__str__() for t in types]
        )


ABITuple.__module__ = "pyteal"


class ABIFixedArray(ABITuple[T]):
    @classmethod
    def decode(cls, value: Expr) -> "ABIFixedArray[T]":
        return cls(value)

    @classmethod
    def __str__(cls):
        types = cls.__orig_bases__[0].__args__[0].__args__
        return "{}[{}]".format(types[0].__str__(), len(types))


ABIFixedArray.__module__ = "pyteal"


class ABIDynamicArray(ABITuple[T]):

    item_len: Uint16

    def __init__(self, data: Expr):
        self.item_len = Uint16.decode(data)
        super().__init__(rest(data, Int(2)))

    @classmethod
    def decode(cls, data: Expr) -> "ABIDynamicArray[T]":
        return cls(data)

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
        return self.encode().__teal__(options)

    def encode(self) -> Expr:
        return Concat(self.item_len.encode(), self.value)

    @classmethod
    def __str__(cls):
        types = cls.__orig_bases__[0].__args__[0].__args__
        return "{}[]".format(types[0].__str__())


ABIDynamicArray.__module__ = "pyteal"
