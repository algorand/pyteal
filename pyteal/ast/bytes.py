from ..types import TealType, valid_base16, valid_base32, valid_base64
from ..errors import TealInputError
from .leafexpr import LeafExpr

class Bytes(LeafExpr):
    """An expression that represents a byte string."""
     
    def __init__(self, base: str, byte_str: str) -> None:
        """Create a new byte string.

        Args:
            base: The base type for this byte string. Must be one of base16, base32, or base64.
            byte_string: The content of the byte string, encoding with the passed in base.
        """
        if base == "base32":
            self.base = base
            valid_base32(byte_str)
            self.byte_str = byte_str
        elif base == "base64":
            self.base = base
            self.byte_str = byte_str
            valid_base64(byte_str)
        elif base == "base16":
            self.base = base
            if byte_str.startswith("0x"):
                self.byte_str = byte_str[2:]
            else:
                self.byte_str = byte_str
            valid_base16(self.byte_str)
        else:
            raise TealInputError("invalid base {}, need to be base32, base64, or base16.".format(base))

    def __teal__(self):
        if self.base != "base16":
            return [["byte", self.base, self.byte_str]]
        else:
            return [["byte", "0x" + self.byte_str]]
        
    def __str__(self):
        return "({} bytes: {})".format(self.base, self.byte_str)

    def type_of(self):
        return TealType.bytes
