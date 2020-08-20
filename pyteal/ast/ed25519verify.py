from ..types import TealType, require_type
from ..ir import TealOp, Op
from .expr import Expr

class Ed25519Verify(Expr):
    """An expression to verify ed25519 signatures."""

    def __init__(self, data: Expr, sig: Expr, key: Expr) -> None:
        """Verify the ed25519 signature of ("ProgData" || program_hash || data).
        
        Args:
            data: The data signed by the public. Must evalutes to bytes.
            sig: The proposed 64 byte signature of ("ProgData" || program_hash || data). Must
                evalute to bytes.
            key: The 32 byte public key that produced the signature. Must evaluate to bytes.
        """
        require_type(data.type_of(), TealType.bytes)
        require_type(sig.type_of(), TealType.bytes)
        require_type(key.type_of(), TealType.bytes)
        
        self.data = data
        self.sig = sig
        self.key = key

    def __teal__(self):
        return self.data.__teal__() + \
               self.sig.__teal__() + \
               self.key.__teal__() + \
               [TealOp(Op.ed25519verify)]

    def __str__(self):
        return "(ed25519verify {} {} {})".format(self.data, self.sig, self.key)

    def type_of(self):
        return TealType.uint64

Ed25519Verify.__module__ = "pyteal"
