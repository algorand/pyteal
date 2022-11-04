from dataclasses import dataclass, field
from itertools import groupby
from typing import TYPE_CHECKING, Optional

from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.abstractvar import AbstractVar
from pyteal.types import TealType, require_type, types_match
from pyteal.errors import TealInputError, TealInternalError, verifyProgramVersion
from pyteal.ir import TealBlock, TealSimpleBlock, TealOp, Op

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


@dataclass
class LocalTypeSegment:
    local_type: TealType
    cnt: int
    auto_instance: Expr = field(init=False)

    def __post_init__(self):
        if self.cnt <= 0:
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
        if self.cnt == 1:
            inst_srt, inst_end = self.auto_instance.__teal__(options)
            return inst_srt, inst_end
        else:
            dupn_srt, dupn_end = DupN(self.auto_instance, self.cnt).__teal__(options)
            return dupn_srt, dupn_end


LocalTypeSegment.__module__ = "pyteal"


@dataclass
class ProtoStackLayout:
    arg_stack_types: list[TealType]
    local_stack_types: list[TealType]
    has_output: bool
    output_index: Optional[int] = field(init=False)
    succinct_repr: list[LocalTypeSegment] = field(init=False)

    def __post_init__(self):
        if self.has_output and len(self.local_stack_types) == 0:
            raise TealInternalError(
                "ProtoStackLayout initialization error: cannot output without local variable allocs."
            )

        self.output_index = 0 if self.has_output else None
        if not all(map(lambda t: types_match(t, TealType.none), self.arg_stack_types)):
            raise TealInternalError("Variables in frame memory layout must be typed.")

        # Type check of local variables are performed over LocalTypeSegments
        self.succinct_repr = [
            LocalTypeSegment(t_type, len(list(dup_seg)))
            for t_type, dup_seg in groupby(self.local_stack_types)
        ]

        # anytype at i + 1 merge to i
        for i in reversed(range(len(self.succinct_repr) - 1)):
            if self.succinct_repr[i + 1].local_type == TealType.anytype:
                self.succinct_repr[i].cnt += self.succinct_repr[i + 1].cnt
                self.succinct_repr.pop(i + 1)

        if (
            len(self.succinct_repr) > 1
            and self.succinct_repr[0].local_type == TealType.anytype
        ):
            self.succinct_repr[1].cnt += self.succinct_repr[0].cnt
            self.succinct_repr.pop(0)

    def __getitem__(self, index: int):
        if index < 0:
            return self.arg_stack_types[len(self.arg_stack_types) + index]
        return self.local_stack_types[index]

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
        /,
        *,
        mem_layout: Optional[ProtoStackLayout] = None,
    ):
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
    def __init__(
        self, frame_index: int, /, *, inferred_type: Optional[TealType] = None
    ):
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
        /,
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
