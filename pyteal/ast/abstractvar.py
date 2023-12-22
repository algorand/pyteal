from abc import ABC, abstractmethod
from pyteal.types import TealType
from pyteal.ast.expr import Expr


class AbstractVar(ABC):
    """AbstractVar is an abstract class that captures properties of a variable.

    A variable, on an abstract perspective, has the following properties:

    * Storing: can be stored to a certain position.
    * Loading: can be loaded from a certain position.
    * (Strong) Typed: can indicate its own type.

    ScratchVar and FrameVar inherits from this class, representing the load and storage of value
    against scratch slots or stack based on frame pointer.

    This class is intentionally hidden because it's too basic to directly expose.
    """

    @abstractmethod
    def store(self, value: Expr) -> Expr:
        """Store value in AbstractVar.

        Args:
            value: An expression that represents the value to store.
        """
        pass

    @abstractmethod
    def load(self) -> Expr:
        """Load value from AbstractVar"""
        pass

    @abstractmethod
    def storage_type(self) -> TealType:
        pass


AbstractVar.__module__ = "pyteal"


def alloc_abstract_var(stack_type: TealType) -> AbstractVar:
    """Allocate abstract var over stack, or over scratch.

    This unexported function takes a TealType as value type representation over stack (or scratch),
    and generates an AbstractVar instance.
    It infers the proto currently being used in context of subroutine evaluation,
    and swap to FrameVar to save the use of scratch slots.

    Arg:
        stack_type: TealType that represents stack type.
    """

    from pyteal.ast.scratchvar import ScratchVar
    from pyteal.ast.subroutine import SubroutineEval
    from pyteal.ast.frame import FrameVar, MAX_FRAME_LOCAL_VARS

    if SubroutineEval._current_proto:
        local_types = SubroutineEval._current_proto.mem_layout.local_stack_types

        # NOTE: you can have at most 128 local variables.
        # len(local_types) + 1 computes the resulting length,
        # should be <= 128
        if len(local_types) + 1 <= MAX_FRAME_LOCAL_VARS:
            local_types.append(stack_type)
            return FrameVar(SubroutineEval._current_proto, len(local_types) - 1)

    return ScratchVar(stack_type)
