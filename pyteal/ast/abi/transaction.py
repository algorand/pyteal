from abc import abstractmethod
from typing import TypeVar, Union, cast
from pyteal.ast.abi.type import BaseType, ComputedValue, TypeSpec
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.txn import TxnType
from pyteal.types import TealType
from pyteal.errors import TealInputError

T = TypeVar("T", bound=BaseType)


class TransactionTypeSpec(TypeSpec):
    def __init__(self) -> None:
        super().__init__()

    def new_instance(self) -> "Transaction":
        return Transaction(self)

    def annotation_type(self) -> "type[Transaction]":
        return Transaction

    def is_dynamic(self) -> bool:
        return False

    def byte_length_static(self) -> int:
        raise TealInputError("Transaction Types don't have a static size")

    def storage_type(self) -> TealType:
        return TealType.uint64

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other)

    @abstractmethod
    def __str__(self) -> str:
        return "txn"


TransactionTypeSpec.__module__ = "pyteal"


class Transaction(BaseType):
    def __init__(self, spec: TransactionTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> TransactionTypeSpec:
        return cast(TransactionTypeSpec, super().type_spec())

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(self: T, value: Union[int, Expr, "Transaction", ComputedValue[T]]) -> Expr:
        match value:
            case ComputedValue():
                self._set_with_computed_type(value)
            case BaseType():
                return self.stored_value.store(self.stored_value.load())
            case int():
                return self.stored_value.store(Int(value))
            case Expr():
                return self.stored_value.store(value)
            case _:
                raise TealInputError(f"Cant store a {type(value)} in a Transaction")

    def validate(self) -> Expr:
        # TODO: make sure the group length is large enough and the index is valid?
        pass

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None,
    ) -> Expr:
        raise TealInputError("A Transaction cannot be decoded")

    def encode(self) -> Expr:
        raise TealInputError("A Transaction cannot be encoded")


Transaction.__module__ = "pyteal"


class AnyTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "Transaction":
        return AnyTransaction()

    def annotation_type(self) -> "type[Transaction]":
        return AnyTransaction

    def __str__(self) -> str:
        return TxnType.Any.name


class AnyTransaction(Transaction):
    def __init__(self):
        super().__init__(AnyTransactionTypeSpec())


class PaymentTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "Transaction":
        return PaymentTransaction()

    def annotation_type(self) -> "type[Transaction]":
        return PaymentTransaction

    def __str__(self) -> str:
        return TxnType.Payment.name


class PaymentTransaction(Transaction):
    def __init__(self):
        super().__init__(PaymentTransactionTypeSpec())


class KeyRegisterTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "Transaction":
        return KeyRegisterTransaction()

    def annotation_type(self) -> "type[Transaction]":
        return KeyRegisterTransaction

    def __str__(self) -> str:
        return TxnType.KeyRegistration.name


class KeyRegisterTransaction(Transaction):
    def __init__(self):
        super().__init__(KeyRegisterTransactionTypeSpec())


class AssetConfigTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "Transaction":
        return AssetConfigTransaction()

    def annotation_type(self) -> "type[Transaction]":
        return AssetConfigTransaction

    def __str__(self) -> str:
        return TxnType.AssetConfig.name


class AssetConfigTransaction(Transaction):
    def __init__(self):
        super().__init__(AssetConfigTransactionTypeSpec())


class AssetFreezeTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "Transaction":
        return AssetFreezeTransaction()

    def annotation_type(self) -> "type[Transaction]":
        return AssetFreezeTransaction

    def __str__(self) -> str:
        return TxnType.AssetFreeze.name


class AssetFreezeTransaction(Transaction):
    def __init__(self):
        super().__init__(AssetFreezeTransactionTypeSpec())


class AssetTransferTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "Transaction":
        return AssetTransferTransaction()

    def annotation_type(self) -> "type[Transaction]":
        return AssetTransferTransaction

    def __str__(self) -> str:
        return TxnType.AssetTransfer.name


class AssetTransferTransaction(Transaction):
    def __init__(self):
        super().__init__(AssetTransferTransactionTypeSpec)


class ApplicationCallTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "Transaction":
        return ApplicationCallTransaction()

    def annotation_type(self) -> "type[Transaction]":
        return ApplicationCallTransaction

    def __str__(self) -> str:
        return TxnType.ApplicationCall


class ApplicationCallTransaction(Transaction):
    def __init__(self):
        super().__init__(ApplicationCallTransactionTypeSpec())
