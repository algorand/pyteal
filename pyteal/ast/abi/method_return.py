from typing import TYPE_CHECKING, Tuple
from pyteal.ast.abi import BaseType
from pyteal.types import TealType
from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.unaryexpr import Log
from pyteal.ast.naryexpr import Concat
from pyteal.ast.bytes import Bytes
from pyteal.config import RETURN_HASH_PREFIX
from pyteal.ir import TealBlock, TealSimpleBlock, Op
from pyteal.stack_frame import NatalStackFrame

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class MethodReturn(Expr):
    def __init__(self, arg: BaseType):
        super().__init__()
        if not isinstance(arg, BaseType):
            raise TealInputError(f"Expecting an ABI type argument but get {arg}")
        self.arg = arg

    def __teal__(self, options: "CompileOptions") -> Tuple[TealBlock, TealSimpleBlock]:
        if options.version < Op.log.min_version:
            raise TealInputError(
                f"current version {options.version} is lower than log's min version {Op.log.min_version}"
            )
        start, end = Log(Concat(Bytes(RETURN_HASH_PREFIX), self.arg.encode())).__teal__(
            options
        )
        NatalStackFrame.reframe_ops_in_blocks(self, start)
        return start, end

    def __str__(self) -> str:
        return f"(MethodReturn {self.arg.type_spec()})"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


MethodReturn.__module__ = "pyteal.abi"
