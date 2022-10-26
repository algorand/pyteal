from typing import TYPE_CHECKING

from pyteal.ast.expr import Expr
from pyteal.types import TealType, require_type
from pyteal.errors import TealInputError, verifyProgramVersion
from pyteal.ir import TealBlock, TealSimpleBlock, TealOp, Op

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Proto(Expr):
    def __init__(self, arg_num: int, ret_num: int):
        super().__init__()
        if arg_num < 0:
            raise TealInputError(f"subroutine arg number {arg_num} must be >= 0")
        if ret_num < 0:
            raise TealInputError(f"return value number {ret_num} must be >= 0")
        self.arg_num = arg_num
        self.ret_num = ret_num

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.proto.min_version,
            options.version,
            "Program version too low to use op proto",
        )
        op = TealOp(self, Op.proto, self.arg_num, self.ret_num)
        return TealBlock.FromOp(options, op)

    def __str__(self) -> str:
        return f"(proto: arg_num = {self.arg_num}, ret_num = {self.ret_num})"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


Proto.__module__ = "pyteal"


class FrameDig(Expr):
    def __init__(self, depth: int):
        super().__init__()
        self.depth = depth

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.frame_dig.min_version,
            options.version,
            "Program version too low to use op frame_dig",
        )
        op = TealOp(self, Op.frame_dig, self.depth)
        return TealBlock.FromOp(options, op)

    def __str__(self) -> str:
        return f"(frame_dig: dig_depth = {self.depth})"

    def type_of(self) -> TealType:
        return TealType.anytype

    def has_return(self) -> bool:
        return False


FrameDig.__module__ = "pyteal"


class FrameBury(Expr):
    def __init__(self, what: Expr, depth: int):
        super().__init__()
        require_type(what, TealType.anytype)
        self.what = what
        self.depth = depth

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.frame_bury.min_version,
            options.version,
            "Program version too low to use op frame_bury",
        )
        op = TealOp(self, Op.frame_bury, self.depth)
        return TealBlock.FromOp(options, op, self.what)

    def __str__(self) -> str:
        return f"(frame_bury (bury_depth = {self.depth}) ({self.what}))"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


FrameBury.__module__ = "pyteal"


class Bury(Expr):
    def __init__(self, what: Expr, depth: int):
        super().__init__()
        require_type(what, TealType.anytype)
        if depth <= 0:
            raise TealInputError("bury depth should be strictly positive")
        self.what = what
        self.depth = depth

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.bury.min_version,
            options.version,
            "Program version too low to use op bury",
        )
        op = TealOp(self, Op.bury, self.depth)
        return TealBlock.FromOp(options, op, self.what)

    def __str__(self) -> str:
        return f"(bury (depth = {self.depth}) ({self.what}))"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


Bury.__module__ = "pyteal"


class DupN(Expr):
    def __init__(self, what: Expr, repetition: int):
        super().__init__()
        require_type(what, TealType.anytype)
        if repetition < 0:
            raise TealInputError("dupn repetition should be non negative")
        self.what = what
        self.repetition = repetition

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.dupn.min_version,
            options.version,
            "Program version too low to use op dupn",
        )
        op = TealOp(self, Op.dupn, self.repetition)
        return TealBlock.FromOp(options, op, self.what)

    def __str__(self) -> str:
        return f"(dupn (repetition = {self.repetition}) ({self.what}))"

    def type_of(self) -> TealType:
        return self.what.type_of()

    def has_return(self) -> bool:
        return False


DupN.__module__ = "pyteal"


class PopN(Expr):
    def __init__(self, repetition: int):
        super().__init__()
        if repetition < 0:
            raise TealInputError("popn repetition should be non negative")
        self.repetition = repetition

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.popn.min_version,
            options.version,
            "Program version too low to use op popn",
        )
        op = TealOp(self, Op.popn, self.repetition)
        return TealBlock.FromOp(options, op)

    def __str__(self) -> str:
        return f"(popn {self.repetition})"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


PopN.__module__ = "pyteal"
