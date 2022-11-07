from itertools import groupby
from typing import TYPE_CHECKING, Optional

from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.abstractvar import AbstractVar
from pyteal.types import TealType, require_type
from pyteal.errors import TealInputError, TealInternalError, verifyProgramVersion
from pyteal.ir import TealBlock, TealSimpleBlock, TealOp, Op

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class LocalTypeSegment(Expr):
    def __init__(self, local_type: TealType, count: int):
        self.local_type = local_type
        self.count = count
        self.auto_instance: Expr

        if self.count <= 0:
            raise TealInternalError(
                "LocalTypeSegment initialization error: segment length must be strictly greatly than 0."
            )
        match self.local_type:
            case TealType.uint64 | TealType.anytype:
                self.auto_instance = Int(0)
            case TealType.bytes:
                self.auto_instance = Bytes("")
            case TealType.none:
                raise TealInternalError(
                    "Local variable in subroutine initialization must be typed."
                )

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        if self.count == 1:
            inst_srt, inst_end = self.auto_instance.__teal__(options)
            return inst_srt, inst_end
        else:
            dupn_srt, dupn_end = DupN(self.auto_instance, self.count).__teal__(options)
            return dupn_srt, dupn_end

    def __str__(self) -> str:
        return f"(LocalTypeSegment: (type: {self.local_type}) (count: {self.count}))"

    def has_return(self) -> bool:
        return False

    def type_of(self) -> TealType:
        return TealType.none


LocalTypeSegment.__module__ = "pyteal"


class ProtoStackLayout(Expr):
    def __init__(
        self,
        arg_stack_types: list[TealType],
        local_stack_types: list[TealType],
        num_returns: int,
    ):
        if num_returns < 0:
            raise TealInternalError("Return number should be non-negative.")
        elif num_returns > len(local_stack_types):
            raise TealInternalError(
                "ProtoStackLayout initialization error:"
                f"return number {num_returns} should not be greater than local allocations {len(local_stack_types)}."
            )

        if not all(map(lambda t: t != TealType.none, arg_stack_types)):
            raise TealInternalError("Variables in frame memory layout must be typed.")

        self.num_returns: int = num_returns
        self.arg_stack_types: list[TealType] = arg_stack_types
        self.local_stack_types: list[TealType] = local_stack_types

        # Type check of local variables are performed over LocalTypeSegments
        self.succinct_repr: list[LocalTypeSegment] = [
            LocalTypeSegment(t_type, len(list(dup_seg)))
            for t_type, dup_seg in groupby(self.local_stack_types)
        ]

    def __getitem__(self, index: int) -> TealType:
        if index < 0:
            return self.arg_stack_types[len(self.arg_stack_types) + index]
        return self.local_stack_types[index]

    def __str__(self) -> str:
        return f"(ProtoStackLayout: (args: {self.arg_stack_types}) (locals: {self.local_stack_types}))"

    def has_return(self) -> bool:
        return False

    def type_of(self) -> TealType:
        return TealType.none

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        seg_srt, seg_end = self.succinct_repr[0].__teal__(options)
        for iter_seg in self.succinct_repr[1:]:
            srt, end = iter_seg.__teal__(options)
            seg_end.setNextBlock(srt)
            seg_end = end
        return seg_srt, seg_end


ProtoStackLayout.__module__ = "pyteal"


class Proto(Expr):
    def __init__(
        self,
        num_args: int,
        num_returns: int,
        *,
        mem_layout: Optional[ProtoStackLayout] = None,
    ):
        super().__init__()
        if num_args < 0:
            raise TealInputError(
                f"The number of arguments provided to Proto must be >= 0 but {num_args=}."
            )
        if num_returns < 0:
            raise TealInputError(
                f"The number of returns provided to Proto must be >= 0 but {num_returns=}."
            )
        if mem_layout:
            if mem_layout.num_returns != num_returns:
                raise TealInternalError(
                    f"The number of returns {num_returns} should match with memory layout's number of returns {mem_layout.num_returns}"
                )
            if len(mem_layout.arg_stack_types) != num_args:
                raise TealInternalError(
                    f"The number of arguments {num_args} should match with memory layout's number of arguments {len(mem_layout.arg_stack_types)}"
                )

        self.num_args = num_args
        self.num_returns = num_returns
        self.mem_layout: Optional[ProtoStackLayout] = mem_layout

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.proto.min_version,
            options.version,
            "Program version too low to use op proto",
        )
        op = TealOp(self, Op.proto, self.num_args, self.num_returns)
        proto_srt, proto_end = TealBlock.FromOp(options, op)
        if not self.mem_layout:
            return proto_srt, proto_end
        local_srt, local_end = self.mem_layout.__teal__(options)
        proto_end.setNextBlock(local_srt)
        return proto_srt, local_end

    def __str__(self) -> str:
        return f"(proto: num_args = {self.num_args}, num_rets = {self.num_returns})"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


Proto.__module__ = "pyteal"


class FrameDig(Expr):
    def __init__(self, frame_index: int, *, inferred_type: Optional[TealType] = None):
        super().__init__()
        self.frame_index = frame_index
        self.dig_type = inferred_type if inferred_type else TealType.anytype

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
        return self.dig_type

    def has_return(self) -> bool:
        return False


FrameDig.__module__ = "pyteal"


class FrameBury(Expr):
    def __init__(
        self,
        value: Expr,
        frame_index: int,
        *,
        validate_types: bool = True,
        inferred_type: Optional[TealType] = None,
    ):
        super().__init__()

        if validate_types:
            target_type = inferred_type if inferred_type else TealType.anytype
            require_type(value, target_type)

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
    def __init__(self, under_proto: Proto, frame_index: int) -> None:
        super().__init__()
        self.proto = under_proto
        self.frame_index = frame_index
        self.stack_type = (
            self.proto.mem_layout[frame_index]
            if self.proto.mem_layout
            else TealType.anytype
        )

    def storage_type(self) -> TealType:
        return self.stack_type

    def store(self, value: Expr, validate_types: bool = True) -> Expr:
        return FrameBury(
            value,
            self.frame_index,
            validate_types=validate_types,
            inferred_type=self.stack_type,
        )

    def load(self) -> Expr:
        return FrameDig(self.frame_index, inferred_type=self.stack_type)


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
