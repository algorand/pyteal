from itertools import groupby
from typing import TYPE_CHECKING, Optional, Final

from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.abstractvar import AbstractVar
from pyteal.types import TealType, require_type
from pyteal.errors import TealInputError, TealInternalError, verifyProgramVersion
from pyteal.ir import TealBlock, TealSimpleBlock, TealOp, Op
from pyteal.stack_frame import NatalStackFrame

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


MAX_FRAME_LOCAL_VARS: Final[int] = 128


class LocalTypeSegment(Expr):
    """An expression that allocates stack spaces for local variable.

    This class is intentionally hidden because it's too basic to directly expose.
    This is only used in ProtoStackLayout internally.
    """

    def __init__(self, local_type: TealType, count: int):
        super().__init__()
        self.local_type = local_type
        self.count = count
        self.auto_instance: Expr

        if self.count <= 0:
            raise TealInternalError(
                "LocalTypeSegment initialization error: segment length must be strictly greater than 0."
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
        return DupN(self.auto_instance, self.count - 1).__teal__(options)

    def __str__(self) -> str:
        return f"(LocalTypeSegment: (type: {self.local_type}) (count: {self.count}))"

    def has_return(self) -> bool:
        return False

    def type_of(self) -> TealType:
        return TealType.none


LocalTypeSegment.__module__ = "pyteal"


class ProtoStackLayout(Expr):
    """An expression that carries arg types and local types for a subroutine.

    Proto return value is placed on frame index 0 against frame pointer,
    and return type is included in local_stack_types, which is the first element.

    This class is intentionally hidden because it's too basic to directly expose.
    This is only used in Proto internally.
    """

    def __init__(
        self,
        arg_stack_types: list[TealType],
        local_stack_types: list[TealType],
        num_return_allocs: int,
    ):
        super().__init__()
        if num_return_allocs < 0:
            raise TealInternalError("Return allocation number should be non-negative.")
        elif num_return_allocs > len(local_stack_types):
            raise TealInternalError(
                "ProtoStackLayout initialization error: "
                f"return allocation number {num_return_allocs} should not "
                f"be greater than local allocations {len(local_stack_types)}."
            )

        if any(t == TealType.none for t in arg_stack_types + local_stack_types):
            raise TealInternalError("Variables in frame memory layout must be typed.")

        self.num_return_allocs: int = num_return_allocs
        self.arg_stack_types: list[TealType] = arg_stack_types
        self.local_stack_types: list[TealType] = local_stack_types

    def __getitem__(self, index: int) -> TealType:
        if index < 0:
            return self.arg_stack_types[len(self.arg_stack_types) + index]
        return self.local_stack_types[index]

    def __str__(self) -> str:
        return f"(ProtoStackLayout: (args: {self.arg_stack_types}) (locals: {self.local_stack_types}))"

    @classmethod
    def from_proto(cls, proto: "Proto") -> "ProtoStackLayout":
        return cls(
            [TealType.anytype] * proto.num_args,
            [TealType.anytype] * proto.num_returns,
            proto.num_returns,
        )

    def has_return(self) -> bool:
        return False

    def type_of(self) -> TealType:
        return TealType.none

    def _succinct_repr(self) -> list[LocalTypeSegment]:
        return [
            LocalTypeSegment(t_type, len(list(dup_seg)))
            for t_type, dup_seg in groupby(self.local_stack_types)
        ]

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        srt = TealSimpleBlock([])
        end = srt

        # Type check of local variables are performed over LocalTypeSegments
        succinct_repr: list[LocalTypeSegment] = self._succinct_repr()
        for iter_seg in succinct_repr:
            seg_srt, seg_end = iter_seg.__teal__(options)
            end.setNextBlock(seg_srt)
            end = seg_end
        return srt, end


ProtoStackLayout.__module__ = "pyteal"


class Proto(Expr):
    """An expression that prepare top call frame for a retsub that will assume A args and R return values.

    Proto return value is placed from frame index 0 against frame pointer.

    This class is intentionally hidden because it's too basic to directly expose.
    It is only used in subroutine, for subroutine declaration computation.
    """

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
        self.num_args = num_args
        self.num_returns = num_returns

        if mem_layout:
            if mem_layout.num_return_allocs > num_returns:
                raise TealInternalError(
                    f"The number of returns {num_returns} should be greater equal to "
                    f"memory layout's number of allocations for returns {mem_layout.num_return_allocs}"
                )
            if len(mem_layout.arg_stack_types) != num_args:
                raise TealInternalError(
                    f"The number of arguments {num_args} should match with "
                    f"memory layout's number of arguments {len(mem_layout.arg_stack_types)}"
                )
        else:
            mem_layout = ProtoStackLayout.from_proto(self)

        self.mem_layout: ProtoStackLayout = mem_layout

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        verifyProgramVersion(
            Op.proto.min_version,
            options.version,
            "Program version too low to use op proto",
        )
        op = TealOp(self, Op.proto, self.num_args, self.num_returns)
        proto_srt, proto_end = TealBlock.FromOp(options, op)
        local_srt, local_end = self.mem_layout.__teal__(options)
        proto_end.setNextBlock(local_srt)
        NatalStackFrame.reframe_ops_in_blocks(self, proto_srt)
        return proto_srt, local_end

    def __str__(self) -> str:
        return f"(proto: num_args = {self.num_args}, num_rets = {self.num_returns})"

    def type_of(self) -> TealType:
        return TealType.none

    def has_return(self) -> bool:
        return False


Proto.__module__ = "pyteal"


class FrameDig(Expr):
    """An expression that digs a value from a position around frame pointer.

    This class is intentionally hidden because it's too basic to directly expose.
    This is used only internally by FrameVar.
    """

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
    """An expression that buries a value to a position around frame pointer.

    This class is intentionally hidden because it's too basic to directly expose.
    This is used only internally by FrameVar.
    """

    def __init__(
        self,
        value: Expr,
        frame_index: int,
        *,
        inferred_type: Optional[TealType] = None,
    ):
        super().__init__()

        target_type: TealType = inferred_type or TealType.anytype
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
    """An instantiation for AbstractVar based on frame pointer.

    FrameVar captures loading, storing and type of variable over stack by frame pointer.

    This class is intentionally hidden because it's too basic to directly expose.
    This is used only internally by SubroutineEval in subroutine declaration computation.
    """

    def __init__(self, under_proto: Proto, frame_index: int) -> None:
        super().__init__()
        self.proto = under_proto
        self.frame_index = frame_index
        self.stack_type = self.proto.mem_layout[frame_index]

    def storage_type(self) -> TealType:
        return self.stack_type

    def store(self, value: Expr) -> Expr:
        return FrameBury(
            value,
            self.frame_index,
            inferred_type=self.stack_type,
        )

    def load(self) -> Expr:
        return FrameDig(self.frame_index, inferred_type=self.stack_type)


FrameVar.__module__ = "pyteal"


class DupN(Expr):
    """Duplicate an expression N times.

    This class is intentionally hidden because it's too basic to directly expose.
    This is used only by Proto and LocalTypeSegment.
    """

    def __init__(self, value: Expr, repetition: int):
        """Create a DupN expression.

        Args:
            value: The value to be duplicated.
            repetition: How many additional times the value should be added to the stack. At the end
                of this operation, `repetition+1` elements will be added to the stack. Zero can be
                specified here to indicate no duplication.
        """
        super().__init__()
        require_type(value, TealType.anytype)
        if repetition < 0:
            raise TealInputError("dupn repetition should be non negative")
        self.value = value
        self.repetition = repetition

    def __teal__(self, options: "CompileOptions") -> tuple[TealBlock, TealSimpleBlock]:
        if self.repetition == 0:
            # no duplication required
            return self.value.__teal__(options)

        if self.repetition == 1:
            # use normal dup op for just 1 duplication
            op = TealOp(self, Op.dup)
            return TealBlock.FromOp(options, op, self.value)

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
