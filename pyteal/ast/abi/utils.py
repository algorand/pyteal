from typing import List

from ...types import TealType
from ..binaryexpr import Op

# Copy/Pasted from pyteal utils for methods that are used in this package


# def accumulate(vals: List[Expr], op: Op) -> Expr:
#     "accumulate recursively pairs elements from the list of expressions passed to return a single value"
#     ops: List[Expr] = []
#     for n in range(0, len(vals) - 1, 2):
#         ops.append(
#             BinaryExpr(op, TealType.uint64, TealType.uint64, vals[n], vals[n + 1])
#         )
#     # If its an odd number, we cant match it, just add the last one
#     if len(vals) % 2 == 1:
#         ops.append(vals[-1])

#     if len(ops) > 1:
#         return accumulate(ops, op)

#     return Seq(ops)


# @Subroutine(TealType.uint64)
# def pow10(x: Int) -> Expr:
#     """Returns 10^x, useful for things like total supply of an asset"""
#     return Exp(Int(10), x)


# # Magic number to convert between ascii chars and integers
# _ascii_zero = 48
# _ascii_nine = _ascii_zero + 9
# ascii_zero = Int(_ascii_zero)
# ascii_nine = Int(_ascii_nine)


# @Subroutine(TealType.uint64)
# def ascii_to_int(arg: Int):
#     """ascii_to_int converts the integer representing a character in ascii to the actual integer it represents"""
#     return Seq(Assert(arg >= ascii_zero), Assert(arg <= ascii_nine), arg - ascii_zero)


# @Subroutine(TealType.bytes)
# def int_to_ascii(arg: Int):
#     """int_to_ascii converts an integer to the ascii byte that represents it"""
#     return Extract(Bytes("0123456789"), arg, Int(1))


# @Subroutine(TealType.uint64)
# def atoi(a: Bytes):
#     """atoi converts a byte string representing a number to the integer value it represents"""
#     return If(
#         Len(a) > Int(0),
#         (ascii_to_int(GetByte(a, Int(0))) * pow10(Len(a) - Int(1)))
#         + atoi(Substring(a, Int(1), Len(a))),
#         Int(0),
#     )


# @Subroutine(TealType.bytes)
# def itoa(i: Int):
#     """itoa converts an integer to the ascii byte string it represents"""
#     return If(
#         i == Int(0),
#         Bytes("0"),
#         Concat(
#             If(i / Int(10) > Int(0), itoa(i / Int(10)), Bytes("")),
#             int_to_ascii(i % Int(10)),
#         ),
#     )


# @Subroutine(TealType.bytes)
# def witoa(i: Bytes):
#     """witoa converts an byte string interpreted as an integer to the ascii byte string it represents"""
#     return If(
#         BitLen(i) == Int(0),
#         Bytes("0"),
#         Concat(
#             If(
#                 BytesGt(BytesDiv(i, Bytes("base16", "A0")), Bytes("base16", "A0")),
#                 witoa(BytesDiv(i, Bytes("base16", "A0"))),
#                 Bytes(""),
#             ),
#             int_to_ascii(Btoi(BytesMod(i, Bytes("base16", "A0")))),
#         ),
#     )


# @Subroutine(TealType.bytes)
# def head(s: Bytes):
#     """head gets the first byte from a bytestring, returns as bytes"""
#     return Extract(s, Int(0), Int(1))


# @Subroutine(TealType.bytes)
# def tail(s: Bytes):
#     """tail returns the string with the first character removed"""
#     return Substring(s, Int(1), Len(s))


# @Subroutine(TealType.bytes)
# def suffix(s: Bytes, n: Int):
#     """suffix returns the last n bytes of a given byte string"""
#     return Substring(s, Len(s) - n, Len(s))


# @Subroutine(TealType.bytes)
# def prefix(s: Bytes, n: Int):
#     """prefix returns the first n bytes of a given byte string"""
#     return Substring(s, Int(0), n)


# @Subroutine(TealType.bytes)
# def rest(s: Bytes, n: Int):
#     """rest returns all bytes after n for a given byte string"""
#     return Substring(s, n, Len(s))
