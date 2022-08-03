from typing import TYPE_CHECKING
from enum import Enum

from pyteal.types import TealType, require_type
from pyteal.errors import verifyFieldVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Base64Encoding(Enum):
    # fmt: off
    #     id  |   name   | min version
    url = (0, "URLEncoding", 7)
    std = (1, "StdEncoding", 7)
    # fmt: on

    def __init__(self, id: int, name: str, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.min_version = min_version


Base64Encoding.__module__ = "pyteal"


class Base64Decode(Expr):
    """An expression that decodes a base64-encoded byte string according to a specific encoding.

    See [RFC 4648](https://rfc-editor.org/rfc/rfc4648.html#section-4) (sections 4 and 5) for information on specifications.

    It is assumed that the encoding ends with the exact number of = padding characters as required by the RFC.
    When padding occurs, any unused pad bits in the encoding must be set to zero or the decoding will fail.
    The special cases of \\n and \\r are allowed but completely ignored. An error will result when attempting
    to decode a string with a character that is not in the encoding alphabet or not one of =, \\r, or \\n.

    NOTE:  Base64Decode usage is not intended for introducing constants. Instead, use :any:`Bytes`.
    """

    def __init__(self, encoding: Base64Encoding, base64: Expr) -> None:
        super().__init__()
        self.encoding = encoding

        require_type(base64, TealType.bytes)
        self.base64 = base64

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(
            self.encoding.arg_name, self.encoding.min_version, options.version
        )

        op = TealOp(self, Op.base64_decode, self.encoding.arg_name)
        return TealBlock.FromOp(options, op, self.base64)

    def __str__(self):
        return "(Base64Decode {})".format(self.encoding.arg_name)

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return False

    @classmethod
    def url(cls, base64: Expr) -> Expr:
        """Decode a base64-encoded byte string according to the URL encoding.

        Refer to the `Base64Decode` class documentation for more information.

        Args:
            base64: A base64-encoded byte string.
        """
        return cls(Base64Encoding.url, base64)

    @classmethod
    def std(cls, base64: Expr) -> Expr:
        """Decode a base64-encoded byte string according to the Standard encoding.

        Refer to the `Base64Decode` class documentation for more information.

        Args:
            base64: A base64-encoded byte string.
        """
        return cls(Base64Encoding.std, base64)


Base64Decode.__module__ = "pyteal"
