from abc import abstractmethod
from typing import TypeVar, Union, cast
from pyteal.ast.abi.type import BaseType, ComputedValue, TypeSpec
from pyteal.ast.expr import Expr
from pyteal.types import TealType
from pyteal.errors import TealInputError

class TransactionTypeSpec(TypeSpec):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def new_instance(self) -> "TransactionType":
        pass

    @abstractmethod
    def annotation_type(self) -> "type[TransactionType]":
        pass

    def is_dynamic(self) -> bool:
        return True 

    def byte_length_static(self) -> int:
        raise TealInputError("Transaction Types don't have a static size")

    def storage_type(self) -> TealType:
        return TealType.none 

    def __eq__(self, other: object) -> bool:
        return False

    def __str__(self) -> str:
        return "txn"


TransactionTypeSpec.__module__ = "pyteal"

T = TypeVar("T", bound=BaseType)


class TransactionType(BaseType):

    @abstractmethod
    def __init__(self, spec: TransactionTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> TransactionTypeSpec:
        return cast(TransactionTypeSpec, super().type_spec())

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(self: T, value: Union[int, Expr, "TransactionType", ComputedValue[T]]) -> Expr:
        pass

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None,
    ) -> Expr:
        pass

    def encode(self) -> Expr:
        pass


TransactionType.__module__ = "pyteal"


#txn represents any Algorand transaction
#pay represents a PaymentTransaction (algo transfer)
#keyreg represents a KeyRegistration transaction (configure consensus participation)
#acfg represent a AssetConfig transaction (create, configure, or destroy ASAs)
#axfer represents an AssetTransfer transaction (ASA transfer)
#afrz represents an AssetFreezeTx transaction (freeze or unfreeze ASAs)
#appl represents an ApplicationCallTx transaction (create/invoke a Smart Contract)