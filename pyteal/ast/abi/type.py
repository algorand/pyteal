from abc import ABC, abstractmethod

from ..expr import Expr


class ABIType(ABC):
    @abstractmethod
    def is_dynamic(self) -> bool:
        pass

    @abstractmethod
    def byte_length_static(self) -> int:
        pass

    @abstractmethod
    def decode(self, encoded: Expr, offset: Expr = None) -> "ABIValue":
        pass


ABIType.__module__ = "pyteal"


class ABIValue(ABC):
    def __init__(self, type: ABIType) -> None:
        super().__init__()
        self.type = type

    def get_type(self) -> ABIType:
        return self.type

    @abstractmethod
    def byte_length(self) -> Expr:
        pass

    @abstractmethod
    def encode(self) -> Expr:
        pass


ABIValue.__module__ = "pyteal"
