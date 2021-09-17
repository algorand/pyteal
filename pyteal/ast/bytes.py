from typing import Union, cast, overload, TYPE_CHECKING

from ..types import TealType, valid_base16, valid_base32, valid_base64
from ..util import escapeStr
from ..ir import TealOp, Op, TealBlock
from ..errors import TealInputError
from .leafexpr import LeafExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Bytes(LeafExpr):
    """An expression that represents a byte string."""

    @overload
    def __init__(self, arg1: Union[str, bytes, bytearray]) -> None:
        ...

    @overload
    def __init__(self, arg1: str, arg2: str) -> None:
        ...

    def __init__(self, arg1: Union[str, bytes, bytearray], arg2: str = None) -> None:
        """Create a new byte string.

        Depending on the encoding, there are different arguments to pass:

        For UTF-8 strings:
            Pass the string as the only argument. For example, ``Bytes("content")``.
        For raw bytes or bytearray objects:
            Pass the bytes or bytearray as the only argument. For example, ``Bytes(b"content")``.
        For base16, base32, or base64 strings:
            Pass the base as the first argument and the string as the second argument. For example,
            ``Bytes("base16", "636F6E74656E74")``, ``Bytes("base32", "ORFDPQ6ARJK")``,
            ``Bytes("base64", "Y29udGVudA==")``.
        Special case for base16:
            The prefix "0x" may be present in a base16 byte string. For example,
            ``Bytes("base16", "0x636F6E74656E74")``.
        """
        super().__init__()
        if arg2 is None:
            if type(arg1) is str:
                self.base = "utf8"
                self.byte_str = escapeStr(arg1)
            elif type(arg1) in (bytes, bytearray):
                self.base = "base16"
                self.byte_str = cast(Union[bytes, bytearray], arg1).hex()
            else:
                raise TealInputError("Unknown argument type: {}".format(type(arg1)))
        else:
            if type(arg1) is not str:
                raise TealInputError("Unknown type for base: {}".format(type(arg1)))

            if type(arg2) is not str:
                raise TealInputError("Unknown type for value: {}".format(type(arg2)))

            self.base = arg1

            if self.base == "base32":
                valid_base32(arg2)
                self.byte_str = arg2
            elif self.base == "base64":
                self.byte_str = arg2
                valid_base64(self.byte_str)
            elif self.base == "base16":
                if arg2.startswith("0x"):
                    self.byte_str = arg2[2:]
                else:
                    self.byte_str = arg2
                valid_base16(self.byte_str)
            else:
                raise TealInputError(
                    "invalid base {}, need to be base32, base64, or base16.".format(
                        self.base
                    )
                )

    def __teal__(self, options: "CompileOptions"):
        if self.base == "utf8":
            payload = self.byte_str
        elif self.base == "base16":
            payload = "0x" + self.byte_str
        else:
            payload = "{}({})".format(self.base, self.byte_str)
        op = TealOp(self, Op.byte, payload)
        return TealBlock.FromOp(options, op)

    def __str__(self):
        return "({} bytes: {})".format(self.base, self.byte_str)

    def type_of(self):
        return TealType.bytes


Bytes.__module__ = "pyteal"
