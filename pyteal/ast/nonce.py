from typing import TYPE_CHECKING

from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq
from pyteal.ast.bytes import Bytes
from pyteal.ast.unaryexpr import Pop

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Nonce(Expr):
    """A meta expression only used to change the hash of a TEAL program."""

    def __init__(self, base: str, nonce: str, child: Expr) -> None:
        """Create a new Nonce.

        The Nonce expression behaves exactly like the child expression passed into it, except it
        uses the provided nonce string to alter its structure in a way that does not affect
        execution.

        Args:
            base: The base of the nonce. Must be one of utf8, base16, base32, or base64.
            nonce: An arbitrary nonce string that conforms to base.
            child: The expression to wrap.
        """
        super().__init__()

        if base not in ("utf8", "base16", "base32", "base64"):
            raise TealInputError("Invalid base: {}".format(base))

        self.child = child
        if base == "utf8":
            self.nonce_bytes = Bytes(nonce)
        else:
            self.nonce_bytes = Bytes(base, nonce)

        self.seq = Seq([Pop(self.nonce_bytes), self.child])

    def __teal__(self, options: "CompileOptions"):
        return self.seq.__teal__(options)

    def __str__(self):
        return "(nonce: {}) {}".format(self.nonce_bytes, self.child)

    def type_of(self):
        return self.child.type_of()

    def has_return(self):
        return self.child.has_return()


Nonce.__module__ = "pyteal"
