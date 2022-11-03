from typing import TYPE_CHECKING

from pyteal.ast.expr import Expr
from pyteal.ast.scratchvar import AbstractVar
from pyteal.types import TealType, require_type
from pyteal.errors import TealInputError, TealInternalError, verifyProgramVersion
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


class FrameVar(AbstractVar):
    def __init__(self, storage_type: TealType, frame_index: int) -> None:
        super().__init__()
        self.stack_type = storage_type
        self.frame_index = frame_index

    def storage_type(self) -> TealType:
        return self.stack_type

    def store(self, value: Expr, validate_types: bool = True) -> Expr:
        if not validate_types:
            # validation always happens inside of FramBury's initializer
            raise TealInternalError(
                f"DynamicScratchVar's must validate_types but {validate_types=}"
            )

        return FrameBury(value, self.frame_index)

    def load(self) -> Expr:
        return FrameDig(self.frame_index)


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
