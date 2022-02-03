from typing import Union, cast

from .. import (
    Assert,
    BitLen,
    Btoi,
    Bytes,
    BytesAdd,
    BytesDiv,
    BytesMinus,
    BytesMul,
    BytesZero,
    Concat,
    GetByte,
    Expr,
    If,
    Int,
    Itob,
    Len,
    ScratchVar,
    Seq,
    Subroutine,
)

from ...types import TealType
from .type import Type

# from .utils import head, itoa, prefix, suffix, tail, witoa, pow10


# def precision_uint8(p: int):
#     return p.to_bytes(8, "big")[-1:]


# @Subroutine(TealType.bytes)
# def byte_precision(v: Bytes):
#     return Itob(pow10(GetByte(v, Int(0))))


# @Subroutine(TealType.none)
# def assert_fp_match(a: Bytes, b: Bytes):
#     return Assert(head(a) == head(b))  # Check precision matches


# @Subroutine(TealType.bytes)
# def check_overflow(prec: Bytes, bytelen: Int, value: Bytes):
#     """check_overflow checks to make sure we didnt overflow and sets the appropriate 0 padding if necessary

#     Args:
#         prec: the precision as bytes
#         bytelen: the number of bytes we expect
#         value: the underlying value, without the precision prefix

#     Returns:
#         appropriately padded bytestring or Asserts if we overflow (overflowed? overflew?)
#     """
#     return Seq(
#         Assert(BitLen(value) / Int(8) <= bytelen),
#         If(
#             Len(value) > bytelen,
#             Concat(
#                 prec, suffix(value, Len(value) - (bytelen - Int(1)))
#             ),  # We can remove zeros
#             Concat(
#                 prec, BytesZero(bytelen - Int(1) - Len(value)), value
#             ),  # We need to pad with zeros
#         ),
#     )


# class UFixed(ABIType):
#     """UFixed represents a numeric value with a fixed number of decimal places

#     From ABI: ufixed<N>x<M>: An N-bit unsigned fixed-point decimal number with precision M, where 8 <= N <= 512, N % 8 = 0, and 0 < M <= 160, which

#     Hold the value in memory as bytes (may be larger than a single uint64)

#     Prepend the precision as a single byte (max precision 160 vs max_uint 255) the number of bits can be computed (Len(bytestring) - 1) * 8
#     Every math operation asserts that the width in bytes of the result is <= to the expected width and repads with 0s if necessary

#     """

#     stack_type = TealType.bytes

#     value: Expr

#     def __init__(self, N: int, M: int):
#         self.bits = N
#         self.precision = M

#     def __call__(self, value: Union[int, float, Expr, Bytes]) -> "UFixed":
#         if type(value) not in [int, float]:
#             raise ValueError

#         if type(value) in (int, float):
#             expected_bytes = self.bits // 8
#             value = Bytes(
#                 int(value * (10 ** self.precision)).to_bytes(expected_bytes, "big")
#             )

#         value = cast(Expr, value)

#         return self.decode(value)

#     def decode(self, value: Expr) -> "UFixed":
#         f = UFixed(self.bits, self.precision)
#         f.value = Concat(Bytes(precision_uint8(self.precision)), value)
#         return f

#     def encode(self):
#         return tail(self.value)

#     def rescaled(self, p: int):
#         rescaled = UFixed(self.bits, p)
#         return rescaled(fp_rescale(self.value, Int(p)))

#     def to_ascii(self):
#         return fp_to_ascii(self.value)

#     def __add__(self, other: "UFixed"):
#         return fp_add(self.value, other.value)

#     def __sub__(self, other: "UFixed"):
#         return fp_sub(self.value, other.value)

#     def __mul__(self, other: "UFixed"):
#         return fp_mul(self.value, other.value)

#     def __truediv__(self, other: "UFixed"):
#         return fp_div(self.value, other.value)

#     def __str__(self):
#         return "ufixed{}x{}".format(self.bits, self.precision)


# UFixed.__module__ = "pyteal"


# @Subroutine(TealType.bytes)
# def fp_add(a: Bytes, b: Bytes):
#     return Seq(
#         assert_fp_match(a, b),
#         check_overflow(head(a), Len(b), BytesAdd(tail(a), tail(b))),
#     )


# @Subroutine(TealType.bytes)
# def fp_sub(a: Bytes, b: Bytes):
#     return Seq(
#         assert_fp_match(a, b),
#         check_overflow(head(a), Len(a), BytesMinus(tail(a), tail(b))),
#     )


# @Subroutine(TealType.bytes)
# def fp_mul(a: Bytes, b: Bytes):
#     return Seq(
#         assert_fp_match(a, b),
#         check_overflow(
#             head(a),
#             Len(a),
#             BytesDiv(
#                 # mul first then divide by the square of the scale
#                 BytesMul(tail(a), tail(b)),
#                 byte_precision(a),
#             ),
#         ),
#     )


# @Subroutine(TealType.bytes)
# def fp_div(a: Bytes, b: Bytes):
#     return Seq(
#         assert_fp_match(a, b),
#         check_overflow(
#             head(a),
#             Len(a),
#             BytesDiv(
#                 # Scale up the numerator so we keep the same precision
#                 BytesMul(tail(a), byte_precision(a)),
#                 tail(b),
#             ),
#         ),
#     )


# @Subroutine(TealType.bytes)
# def fp_rescale(v: Bytes, p: Int):
#     return check_overflow(
#         # Prepend new precision byte
#         suffix(Itob(p), Int(1)),
#         Len(v),
#         # Divide off the old precision
#         BytesDiv(
#             # Multiply by new precision first so we dont lose precision
#             BytesMul(tail(v), Itob(pow10(p))),
#             byte_precision(v),
#         ),
#     )


# @Subroutine(TealType.bytes)
# def fp_to_ascii(v: Bytes):
#     val = tail(v)
#     prec = GetByte(v, Int(-2))
#     ascii = ScratchVar()

#     return Seq(
#         If(Len(val) > Int(6), ascii.store(witoa(val)), ascii.store(itoa(Btoi(val)))),
#         Concat(
#             prefix(ascii.load(), Len(ascii.load()) - prec),
#             Bytes("."),
#             suffix(ascii.load(), prec),
#         ),
#     )
