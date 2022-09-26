from typing import cast, overload, TYPE_CHECKING

from pyteal.types import TealType, valid_base16, valid_base32, valid_base64
from pyteal.util import escapeStr
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.errors import TealInputError
from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Bytes(LeafExpr):
    """An expression that represents a byte string."""

    base: str  # Literal["utf8","base16", "base32", "base64"]
    byte_str: str

    @overload
    def __init__(self, arg1: str | bytes | bytearray) -> None:  # overload_0
        pass

    @overload
    def __init__(self, arg1: str, arg2: str) -> None:  # overload_1
        pass

    def __init__(
        self, arg1: str | bytes | bytearray | str, arg2: None | str = None
    ) -> None:
        """
        __init__(arg1: Union[str, bytes, bytearray]) -> None
        __init__(self, arg1: str, arg2: str) -> None

        Create a new byte string.

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

        # overload_0, Bytes(arg1: str | bytes | bytearray)
        if arg2 is None:
            if type(arg1) is str:
                self.base = "utf8"
                self.byte_str = escapeStr(arg1)
                return
            elif type(arg1) in (bytes, bytearray):
                self.base = "base16"
                self.byte_str = cast(bytes | bytearray, arg1).hex()
                return
            else:
                raise TealInputError(f"Unknown argument type: {type(arg1)}")

        # overload_1, Bytes(self, arg1: str, arg2: str)
        valid_bases = ("base16", "base32", "base64")
        if type(arg1) is not str:
            raise TealInputError(f"Unknown type for value: {type(arg1)}")
        if arg1 not in valid_bases:
            raise TealInputError(f"invalid base {arg1}, need to be in {valid_bases}")
        if type(arg2) is not str:
            raise TealInputError(f"Unknown type for value: {type(arg2)}")

        self.base = arg1
        self.byte_str = arg2
        if self.base == "base16" and arg2.startswith("0x"):
            self.byte_str = self.byte_str[2:]
        validate_method = {
            "base16": valid_base16,
            "base32": valid_base32,
            "base64": valid_base64,
        }
        validate_method[self.base](self.byte_str)

    def __teal__(self, options: "CompileOptions"):
        if self.base == "utf8":
            payload = self.byte_str
        elif self.base == "base16":
            payload = "0x" + self.byte_str
        else:
            payload = f"{self.base}({self.byte_str})"
        op = TealOp(self, Op.byte, payload)
        return TealBlock.FromOp(options, op)

    def __str__(self):
        return f"({self.base} bytes: {self.byte_str})"

    def type_of(self):
        return TealType.bytes


Bytes.__module__ = "pyteal"
