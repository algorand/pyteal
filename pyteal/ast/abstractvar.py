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

        In most cases, we validate the type of the value to store against the type of the :any:`AbstractVar`.
        The *only* case we skip type validation is:
        we store a :any:`ReturnValue` of an :code:`ABIReturnSubroutine` into an :any:`AbstractVar`.
        An :any:`ABIReturnSubroutine` evaluates to :code:`TealType.none`,
        while an :any:`AbstractVar` has any concrete type other than :code:`TealType.none`.
        A direct type check against :any:`ABIReturnSubroutine` will incur a type error,
        while we apply type check against output keyword argument of :any:`ABIReturnSubroutine`,
        which is applied and enforced inside :any:`ReturnedValue`.

        In short, in most scenarios, we do not recommended to let validate_type to be False,
        unless one is very clear about the expected behavior.

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
