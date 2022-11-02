from abc import ABC, abstractmethod
from pyteal.types import TealType
from pyteal.ast.expr import Expr


class AbstractVar(ABC):
    @abstractmethod
    def store(self, value: Expr, validate_types: bool = True) -> Expr:
        pass

    @abstractmethod
    def load(self) -> Expr:
        pass

    @abstractmethod
    def storage_type(self) -> TealType:
        pass


AbstractVar.__module__ = "pyteal"
