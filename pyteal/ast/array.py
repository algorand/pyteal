from abc import ABC, abstractmethod

from .expr import Expr


class Array(ABC):
    """Represents a variable length array of objects."""

    @abstractmethod
    def length(self) -> Expr:
        """Get the length of the array."""
        pass

    @abstractmethod
    def __getitem__(self, index: int):
        """Get the value at a given index in this array."""
        pass


Array.__module__ = "pyteal"
