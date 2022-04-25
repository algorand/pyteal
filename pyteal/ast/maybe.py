from typing import List, Union

from pyteal.ast.multi import MultiValue

from pyteal.types import TealType
from pyteal.ir import Op
from pyteal.ast.expr import Expr
from pyteal.ast.scratch import ScratchLoad, ScratchSlot


class MaybeValue(MultiValue):
    """Represents a get operation returning a value that may not exist."""

    def __init__(
        self,
        op: Op,
        type: TealType,
        *,
        immediate_args: List[Union[int, str]] = None,
        args: List[Expr] = None
    ):
        """Create a new MaybeValue.

        Args:
            op: The operation that returns values.
            type: The type of the returned value.
            immediate_args (optional): Immediate arguments for the op. Defaults to None.
            args (optional): Stack arguments for the op. Defaults to None.
        """
        types = [type, TealType.uint64]
        super().__init__(op, types, immediate_args=immediate_args, args=args)

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

        Note: This is mainly added for backwards compatability and normally shouldn't be used
        directly in pyteal code.
        """
        return self.output_slots[1]

    @property
    def slotValue(self) -> ScratchSlot:
        """Get the scratch slot that stores the value or the zero value for the type if the value
        doesn't exist.

        Note: This is mainly added for backwards compatability and normally shouldn't be used
        directly in pyteal code.
        """
        return self.output_slots[0]


MaybeValue.__module__ = "pyteal"
