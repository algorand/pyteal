from typing import TYPE_CHECKING

from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.scratchvar import AbstractVar
from pyteal.types import TealType, require_type, types_match
from pyteal.errors import TealInputError, verifyProgramVersion
from pyteal.ir import TealBlock, TealSimpleBlock, TealOp, Op

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Proto(Expr):
    def __init__(self, num_args: int, num_returns: int, /, *, num_local_vars: int = 0):
        super().__init__()
        if num_args < 0:
            raise TealInputError(
                f"the number of arguments provided to Proto must be >= 0 but {num_args=}"
            )
        if num_returns < 0:
            raise TealInputError(
                f"the number of return values provided to Proto must be >= 0 but {num_returns=}"
            )
        self.num_args = num_args
        self.num_returns = num_returns
        self.num_local_vars = num_local_vars

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.proto.min_version,
            options.version,
            "Program version too low to use op proto",
        )
        op = TealOp(self, Op.proto, self.num_args, self.num_returns)
        proto_srt, proto_end = TealBlock.FromOp(options, op)
        if self.num_local_vars == 0:
            return proto_srt, proto_end
        elif self.num_local_vars == 1:
            int_srt, int_end = Int(0).__teal__(options)
            proto_end.setNextBlock(int_srt)
            return proto_srt, int_end
        else:
            dupn_srt, dupn_end = DupN(Int(0), self.num_local_vars).__teal__(options)
            proto_end.setNextBlock(dupn_srt)
            return proto_srt, dupn_end

    def __str__(self) -> str:
        return f"(proto: num_args = {self.num_args}, num_rets = {self.num_returns}, num_local_vars = {self.num_local_vars})"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


Proto.__module__ = "pyteal"


class FrameDig(Expr):
    def __init__(self, frame_index: int):
        super().__init__()
        self.frame_index = frame_index

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.frame_dig.min_version,
            options.version,
            "Program version too low to use op frame_dig",
        )
        op = TealOp(self, Op.frame_dig, self.frame_index)
        return TealBlock.FromOp(options, op)

    def __str__(self) -> str:
        return f"(frame_dig: dig_from = {self.frame_index})"

    def type_of(self) -> TealType:
        return TealType.anytype

    def has_return(self) -> bool:
        return False


FrameDig.__module__ = "pyteal"


class FrameBury(Expr):
    def __init__(self, value: Expr, frame_index: int):
        from pyteal.ast.subroutine import SubroutineCall

        super().__init__()
        if not isinstance(value, SubroutineCall) or not value.output_kwarg:
            require_type(value, TealType.anytype)
        else:
            assert types_match(
                value.output_kwarg.abi_type.storage_type(), TealType.anytype
            )

        self.value = value
        self.frame_index = frame_index

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.frame_bury.min_version,
            options.version,
            "Program version too low to use op frame_bury",
        )
        op = TealOp(self, Op.frame_bury, self.frame_index)
        return TealBlock.FromOp(options, op, self.value)

    def __str__(self) -> str:
        return f"(frame_bury (bury_to = {self.frame_index}) ({self.value}))"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


FrameBury.__module__ = "pyteal"


class FrameVar(AbstractVar):
    def __init__(self, storage_type: TealType, stack_depth: int) -> None:
        super().__init__()
        self.stack_type = storage_type
        self.stack_depth = stack_depth

    def storage_type(self) -> TealType:
        return self.stack_type

    def store(self, value: Expr) -> Expr:
        from pyteal.ast import FrameBury

        return FrameBury(value, self.stack_depth)

    def load(self) -> Expr:
        from pyteal.ast import FrameDig

        return FrameDig(self.stack_depth)


FrameVar.__module__ = "pyteal"


class DupN(Expr):
    def __init__(self, value: Expr, repetition: int):
        super().__init__()
        require_type(value, TealType.anytype)
        if repetition < 0:
            raise TealInputError("dupn repetition should be non negative")
        self.value = value
        self.repetition = repetition

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.dupn.min_version,
            options.version,
            "Program version too low to use op dupn",
        )
        op = TealOp(self, Op.dupn, self.repetition)
        return TealBlock.FromOp(options, op, self.value)

    def __str__(self) -> str:
        return f"(dupn (repetition = {self.repetition}) ({self.value}))"

    def type_of(self) -> TealType:
        return self.value.type_of()

    def has_return(self) -> bool:
        return False


DupN.__module__ = "pyteal"
