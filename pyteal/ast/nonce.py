from ..errors import TealInputError
from .expr import Expr
from ..ir import TealOp, Op
from .seq import Seq
from .bytes import Bytes
from .unaryexpr import Pop

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
        if base not in ("utf8", "base16", "base32", "base64"):
            raise TealInputError("Invalid base: {}".format(base))

        self.child = child
        if base == "utf8":
            self.nonce_bytes = Bytes(nonce)
        else:
            self.nonce_bytes = Bytes(base, nonce)

    def __teal__(self):
        return Seq([
            Pop(self.nonce_bytes),
            self.child
        ]).__teal__()

    def __str__(self):
        return "(nonce: {}) {}".format(self.nonce_bytes.__str__(), self.child.__str__())

    def type_of(self):
        return self.child.type_of()

Nonce.__module__ = "pyteal"
