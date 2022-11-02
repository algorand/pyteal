from enum import Enum
from typing import Union, cast, Final
from pyteal.ast.abi.type import BaseType, ComputedValue, TypeSpec
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.txn import TxnObject, TxnType
from pyteal.ast.gtxn import Gtxn
from pyteal.types import TealType
from pyteal.errors import TealInputError, TealInternalError


class TransactionType(Enum):
    Any = "txn"
    Payment = "pay"
    KeyRegistration = "keyreg"
    AssetConfig = "acfg"
    AssetTransfer = "axfer"
    AssetFreeze = "afrz"
    ApplicationCall = "appl"


TransactionType.__module__ = "pyteal.abi"


class TransactionTypeSpec(TypeSpec):
    def __init__(self) -> None:
        super().__init__()

    def new_instance(self) -> "Transaction":
        return Transaction()

    def annotation_type(self) -> "type[Transaction]":
        return Transaction

    def is_dynamic(self) -> bool:
        return False

    def byte_length_static(self) -> int:
        raise TealInputError("Transaction Types don't have a static size")

    def storage_type(self) -> TealType:
        return TealType.uint64

    def txn_type_enum(self) -> Expr:
        """Get the integer transaction type value this TransactionTypeSpec represents.

        See :any:`TxnType` for the complete list.

        If this is a generic TransactionTypeSpec, i.e. type :code:`txn`, this method will raise an error, since this type does not represent a single transaction type.
        """
        raise TealInternalError(
            "abi.TransactionTypeSpec does not represent a specific transaction type"
        )

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other)

    def __str__(self) -> str:
        return TransactionType.Any.value


TransactionTypeSpec.__module__ = "pyteal.abi"


class Transaction(BaseType):
    def __init__(self, spec: TransactionTypeSpec = None) -> None:
        if spec is None:
            super().__init__(TransactionTypeSpec())
        else:
            super().__init__(spec)

    def type_spec(self) -> TransactionTypeSpec:
        return cast(TransactionTypeSpec, super().type_spec())

    def get(self) -> TxnObject:
        return Gtxn[self.index()]

    def _set_index(
        self, value: Union[int, Expr, "Transaction", ComputedValue["Transaction"]]
    ) -> Expr:
        match value:
            case ComputedValue():
                return self._set_with_computed_type(value)
            case BaseType():
                return self.stored_value.store(self.stored_value.load())
            case int():
                return self.stored_value.store(Int(value))
            case Expr():
                return self.stored_value.store(value)
            case _:
                raise TealInputError(f"Cant store a {type(value)} in a Transaction")

    def index(self) -> Expr:
        return self.stored_value.load()

    def decode(
        self,
        encoded: Expr,
        *,
        start_index: Expr = None,
        end_index: Expr = None,
        length: Expr = None,
    ) -> Expr:
        raise TealInputError("A Transaction cannot be decoded")

    def encode(self) -> Expr:
        raise TealInputError("A Transaction cannot be encoded")


Transaction.__module__ = "pyteal.abi"


class PaymentTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "PaymentTransaction":
        return PaymentTransaction()

    def annotation_type(self) -> "type[PaymentTransaction]":
        return PaymentTransaction

    def txn_type_enum(self) -> Expr:
        return TxnType.Payment

    def __str__(self) -> str:
        return TransactionType.Payment.value


PaymentTransactionTypeSpec.__module__ = "pyteal.abi"


class PaymentTransaction(Transaction):
    def __init__(self):
        super().__init__(PaymentTransactionTypeSpec())


PaymentTransaction.__module__ = "pyteal.abi"


class KeyRegisterTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "KeyRegisterTransaction":
        return KeyRegisterTransaction()

    def annotation_type(self) -> "type[KeyRegisterTransaction]":
        return KeyRegisterTransaction

    def txn_type_enum(self) -> Expr:
        return TxnType.KeyRegistration

    def __str__(self) -> str:
        return TransactionType.KeyRegistration.value


KeyRegisterTransactionTypeSpec.__module__ = "pyteal.abi"


class KeyRegisterTransaction(Transaction):
    def __init__(self):
        super().__init__(KeyRegisterTransactionTypeSpec())


KeyRegisterTransaction.__module__ = "pyteal.abi"


class AssetConfigTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "AssetConfigTransaction":
        return AssetConfigTransaction()

    def annotation_type(self) -> "type[AssetConfigTransaction]":
        return AssetConfigTransaction

    def txn_type_enum(self) -> Expr:
        return TxnType.AssetConfig

    def __str__(self) -> str:
        return TransactionType.AssetConfig.value


AssetConfigTransactionTypeSpec.__module__ = "pyteal.abi"


class AssetConfigTransaction(Transaction):
    def __init__(self):
        super().__init__(AssetConfigTransactionTypeSpec())


AssetConfigTransaction.__module__ = "pyteal.abi"


class AssetFreezeTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "AssetFreezeTransaction":
        return AssetFreezeTransaction()

    def annotation_type(self) -> "type[AssetFreezeTransaction]":
        return AssetFreezeTransaction

    def txn_type_enum(self) -> Expr:
        return TxnType.AssetFreeze

    def __str__(self) -> str:
        return TransactionType.AssetFreeze.value


AssetFreezeTransactionTypeSpec.__module__ = "pyteal.abi"


class AssetFreezeTransaction(Transaction):
    def __init__(self):
        super().__init__(AssetFreezeTransactionTypeSpec())


AssetFreezeTransaction.__module__ = "pyteal.abi"


class AssetTransferTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "AssetTransferTransaction":
        return AssetTransferTransaction()

    def annotation_type(self) -> "type[AssetTransferTransaction]":
        return AssetTransferTransaction

    def txn_type_enum(self) -> Expr:
        return TxnType.AssetTransfer

    def __str__(self) -> str:
        return TransactionType.AssetTransfer.value


AssetTransferTransactionTypeSpec.__module__ = "pyteal.abi"


class AssetTransferTransaction(Transaction):
    def __init__(self):
        super().__init__(AssetTransferTransactionTypeSpec())


AssetTransferTransaction.__module__ = "pyteal.abi"


class ApplicationCallTransactionTypeSpec(TransactionTypeSpec):
    def new_instance(self) -> "ApplicationCallTransaction":
        return ApplicationCallTransaction()

    def annotation_type(self) -> "type[ApplicationCallTransaction]":
        return ApplicationCallTransaction

    def txn_type_enum(self) -> Expr:
        return TxnType.ApplicationCall

    def __str__(self) -> str:
        return TransactionType.ApplicationCall.value


ApplicationCallTransactionTypeSpec.__module__ = "pyteal.abi"


class ApplicationCallTransaction(Transaction):
    def __init__(self):
        super().__init__(ApplicationCallTransactionTypeSpec())


ApplicationCallTransaction.__module__ = "pyteal.abi"

TransactionTypeSpecs: Final[list[TypeSpec]] = [
    TransactionTypeSpec(),
    PaymentTransactionTypeSpec(),
    KeyRegisterTransactionTypeSpec(),
    AssetConfigTransactionTypeSpec(),
    AssetFreezeTransactionTypeSpec(),
    AssetTransferTransactionTypeSpec(),
    ApplicationCallTransactionTypeSpec(),
]
