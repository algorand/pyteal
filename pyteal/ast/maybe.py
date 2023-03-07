from typing import Callable, List, Union, TYPE_CHECKING

from pyteal.errors import verifyProgramVersion
from pyteal.types import TealType
from pyteal.ir import Op

from pyteal.ast.expr import Expr
from pyteal.ast.scratch import ScratchLoad, ScratchSlot
from pyteal.ast.multi import MultiValue

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class MaybeValue(MultiValue):
    """Represents a get operation returning a value that may not exist."""

    def __init__(
        self,
        op: Op,
        type: TealType,
        *,
        immediate_args: List[Union[int, str]] | None = None,
        args: List[Expr] | None = None,
        compile_check: Callable[["CompileOptions"], None] | None = None,
    ):
        """Create a new MaybeValue.

        Args:
            op: The operation that returns values.
            type: The type of the returned value.
            immediate_args (optional): Immediate arguments for the op. Defaults to None.
            args (optional): Stack arguments for the op. Defaults to None.
            compile_check (optional): Callable compile check. Defaults to program version check.
                This parameter overwrites the default program version check.
        """

        # Default compile check if one is not given
        def local_version_check(options: "CompileOptions"):
            verifyProgramVersion(
                minVersion=op.min_version,
                version=options.version,
                msg=f"{op.value} unavailable",
            )

        types = [type, TealType.uint64]
        super().__init__(
            op,
            types,
            immediate_args=immediate_args,
            args=args,
            compile_check=(
                local_version_check if compile_check is None else compile_check
            ),
            root_expr=self,
        )

    def hasValue(self) -> ScratchLoad:
        """Check if the value exists.

        This will return 1 if the value exists, otherwise 0.
        """
        return self.output_slots[1].load(self.types[1])

    def value(self) -> ScratchLoad:
        """Get the value.

        If the value exists, it will be returned. Otherwise, the zero value for this type will be
        returned (i.e. either 0 or an empty byte string, depending on the type).
        """
        return self.output_slots[0].load(self.types[0])

    @property
    def slotOk(self) -> ScratchSlot:
        """Get the scratch slot that stores hasValue.

        Note: This is mainly added for backwards compatibility and normally shouldn't be used
        directly in pyteal code.
        """
        return self.output_slots[1]

    @property
    def slotValue(self) -> ScratchSlot:
        """Get the scratch slot that stores the value or the zero value for the type if the value
        doesn't exist.

        Note: This is mainly added for backwards compatibility and normally shouldn't be used
        directly in pyteal code.
        """
        return self.output_slots[0]


MaybeValue.__module__ = "pyteal"
