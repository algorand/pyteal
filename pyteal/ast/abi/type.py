from typing import TypeVar
from abc import ABC, abstractmethod

from ...types import TealType
from ..expr import Expr
from ..scratchvar import ScratchVar

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
    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> Expr:
        pass


Type.__module__ = "pyteal"
