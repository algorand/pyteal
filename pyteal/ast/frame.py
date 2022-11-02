from typing import TYPE_CHECKING

from pyteal.ast.expr import Expr
from pyteal.types import TealType, require_type
from pyteal.errors import TealInputError, verifyProgramVersion
from pyteal.ir import TealBlock, TealSimpleBlock, TealOp, Op

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Proto(Expr):
    def __init__(self, num_args: int, num_returns: int):
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

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.proto.min_version,
            options.version,
            "Program version too low to use op proto",
        )
        op = TealOp(self, Op.proto, self.num_args, self.num_returns)
        return TealBlock.FromOp(options, op)

    def __str__(self) -> str:
        return f"(proto: num_args = {self.num_args}, num_returns = {self.num_returns})"

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
        super().__init__()
        require_type(value, TealType.anytype)
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
