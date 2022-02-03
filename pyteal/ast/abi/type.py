from typing import TypeVar, Generic, Callable
from abc import ABC, abstractmethod

from ...types import TealType
from ..expr import Expr
from ..scratchvar import ScratchVar
from ..seq import Seq

T = TypeVar("T", bound="Type")


class Type(ABC):
    def __init__(self, valueType: TealType) -> None:
        super().__init__()
        self.stored_value = ScratchVar(valueType)

    @abstractmethod
    def has_same_type_as(self, other: "Type") -> bool:
        pass

    @abstractmethod
    def new_instance(self: T) -> T:
        pass

    @abstractmethod
    def is_dynamic(self) -> bool:
        pass

    @abstractmethod
    def byte_length_static(self) -> int:
        pass

    @abstractmethod
    def encode(self) -> Expr:
        pass

    @abstractmethod
    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


Type.__module__ = "pyteal"


class ComputedType(ABC, Generic[T]):
    def __init__(self, producedType: T) -> None:
        super().__init__()
        self._producedType = producedType

    @abstractmethod
    def store_into(self, output: T) -> Expr:
        pass

    def use(self, action: Callable[[T], Expr]) -> Expr:
        newInstance = self._producedType.new_instance()
        return Seq(self.store_into(newInstance), action(newInstance))


ComputedType.__module__ = "pyteal"
