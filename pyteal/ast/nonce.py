from .expr import Expr
from .bytes import Bytes

class Nonce(Expr):
    """A meta expression only used to change the hash of a TEAL program."""

    def __init__(self, base: str, nonce: str, child: Expr) -> None:
        """Create a new Nonce.
        
        The Nonce expression behaves exactly like the child expression passed into it, except it
        uses the provided nonce string to alter its structure in a way that does not affect
        execution.
        
        Args:
            base: The base of the nonce. Must be one of base16, base32, or base64.
            nonce: An arbitrary nonce string.
            child: The expression to wrap.
        """
        self.child = child
        self.nonce_bytes = Bytes(base, nonce)

    def __teal__(self):
        return self.nonce_bytes.__teal__() + [["pop"]] + self.child.__teal__()
        
    def __str__(self):
        return "(nonce: {}) {}".format(self.nonce_bytes.__str__(), self.child.__str__())

    def type_of(self):
        return self.child.type_of()
