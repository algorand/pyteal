from ..types import TealType, valid_base16, valid_base32, valid_base64
from ..util import escapeStr
from ..ir import TealOp, Op
from ..errors import TealInputError
from .leafexpr import LeafExpr

class Bytes(LeafExpr):
    """An expression that represents a byte string."""
    
    def __init__(self, *args: str) -> None:
        """Create a new byte string.
        
        Depending on the encoding, there are different arguments to pass:

        For UTF-8 strings:
            Pass the string as the only argument. For example, ``Bytes("content")``.
        For base16, base32, or base64 strings:
            Pass the base as the first argument and the string as the second argument. For example,
            ``Bytes("base16", "636F6E74656E74")``, ``Bytes("base32", "ORFDPQ6ARJK")``,
            ``Bytes("base64", "Y29udGVudA==")``.
        Special case for base16:
            The prefix "0x" may be present in a base16 byte string. For example,
            ``Bytes("base16", "0x636F6E74656E74")``.
        """
        if len(args) == 1:
            self.base = "utf8"
            self.byte_str = escapeStr(args[0])
        elif len(args) == 2:
            self.base, byte_str = args
            if self.base == "base32":
                valid_base32(byte_str)
                self.byte_str = byte_str
            elif self.base == "base64":
                self.byte_str = byte_str
                valid_base64(byte_str)
            elif self.base == "base16":
                if byte_str.startswith("0x"):
                    self.byte_str = byte_str[2:]
                else:
                    self.byte_str = byte_str
                valid_base16(self.byte_str)
            else:
                raise TealInputError("invalid base {}, need to be base32, base64, or base16.".format(self.base))
        else:
            raise TealInputError("Only 1 or 2 arguments are expected for Bytes constructor, you provided {}".format(len(args)))

    def __teal__(self):
        if self.base == "utf8":
            payload = self.byte_str
        elif self.base == "base16":
            payload = "0x" + self.byte_str
        else:
            payload = "{}({})".format(self.base, self.byte_str)
        return [TealOp(Op.byte, payload)]

    def __str__(self):
        return "({} bytes: {})".format(self.base, self.byte_str)

    def type_of(self):
        return TealType.bytes

Bytes.__module__ = "pyteal"
