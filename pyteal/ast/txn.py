from enum import Enum
from typing import Callable, Optional, Union, cast, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.errors import (
    TealInputError,
    TealCompileError,
    verifyFieldVersion,
    verifyProgramVersion,
)
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.leafexpr import LeafExpr
from pyteal.ast.expr import Expr
from pyteal.ast.int import EnumInt
from pyteal.ast.array import Array

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class TxnType:
    """Enum of all possible transaction types."""

    Unknown = EnumInt("unknown")  # T2PT7
    Payment = EnumInt("pay")  # T2PT7
    KeyRegistration = EnumInt("keyreg")  # T2PT7
    AssetConfig = EnumInt("acfg")  # T2PT7
    AssetTransfer = EnumInt("axfer")  # T2PT7
    AssetFreeze = EnumInt("afrz")  # T2PT7
    ApplicationCall = EnumInt("appl")  # T2PT7


TxnType.__module__ = "pyteal"


class TxnField(Enum):
    sender = (0, "Sender", TealType.bytes, False, 2)
    fee = (1, "Fee", TealType.uint64, False, 2)
    first_valid = (2, "FirstValid", TealType.uint64, False, 2)
    first_valid_time = (3, "FirstValidTime", TealType.uint64, False, 7)
    last_valid = (4, "LastValid", TealType.uint64, False, 2)
    note = (5, "Note", TealType.bytes, False, 2)
    lease = (6, "Lease", TealType.bytes, False, 2)
    receiver = (7, "Receiver", TealType.bytes, False, 2)
    amount = (8, "Amount", TealType.uint64, False, 2)
    close_remainder_to = (9, "CloseRemainderTo", TealType.bytes, False, 2)
    vote_pk = (10, "VotePK", TealType.bytes, False, 2)
    selection_pk = (11, "SelectionPK", TealType.bytes, False, 2)
    vote_first = (12, "VoteFirst", TealType.uint64, False, 2)
    vote_last = (13, "VoteLast", TealType.uint64, False, 2)
    vote_key_dilution = (14, "VoteKeyDilution", TealType.uint64, False, 2)
    type = (15, "Type", TealType.bytes, False, 2)
    type_enum = (16, "TypeEnum", TealType.uint64, False, 2)
    xfer_asset = (17, "XferAsset", TealType.uint64, False, 2)
    asset_amount = (18, "AssetAmount", TealType.uint64, False, 2)
    asset_sender = (19, "AssetSender", TealType.bytes, False, 2)
    asset_receiver = (20, "AssetReceiver", TealType.bytes, False, 2)
    asset_close_to = (21, "AssetCloseTo", TealType.bytes, False, 2)
    group_index = (22, "GroupIndex", TealType.uint64, False, 2)
    tx_id = (23, "TxID", TealType.bytes, False, 2)
    application_id = (24, "ApplicationID", TealType.uint64, False, 2)
    on_completion = (25, "OnCompletion", TealType.uint64, False, 2)
    application_args = (26, "ApplicationArgs", TealType.bytes, True, 2)
    num_app_args = (27, "NumAppArgs", TealType.uint64, False, 2)
    accounts = (28, "Accounts", TealType.bytes, True, 2)
    num_accounts = (2, "NumAccounts", TealType.uint64, False, 2)
    approval_program = (30, "ApprovalProgram", TealType.bytes, False, 2)
    clear_state_program = (31, "ClearStateProgram", TealType.bytes, False, 2)
    rekey_to = (32, "RekeyTo", TealType.bytes, False, 2)
    config_asset = (33, "ConfigAsset", TealType.uint64, False, 2)
    config_asset_total = (34, "ConfigAssetTotal", TealType.uint64, False, 2)
    config_asset_decimals = (35, "ConfigAssetDecimals", TealType.uint64, False, 2)
    config_asset_default_frozen = (
        36,
        "ConfigAssetDefaultFrozen",
        TealType.uint64,
        False,
        2,
    )
    config_asset_unit_name = (37, "ConfigAssetUnitName", TealType.bytes, False, 2)
    config_asset_name = (38, "ConfigAssetName", TealType.bytes, False, 2)
    config_asset_url = (39, "ConfigAssetURL", TealType.bytes, False, 2)
    config_asset_metadata_hash = (
        40,
        "ConfigAssetMetadataHash",
        TealType.bytes,
        False,
        2,
    )
    config_asset_manager = (41, "ConfigAssetManager", TealType.bytes, False, 2)
    config_asset_reserve = (42, "ConfigAssetReserve", TealType.bytes, False, 2)
    config_asset_freeze = (43, "ConfigAssetFreeze", TealType.bytes, False, 2)
    config_asset_clawback = (44, "ConfigAssetClawback", TealType.bytes, False, 2)
    freeze_asset = (45, "FreezeAsset", TealType.uint64, False, 2)
    freeze_asset_account = (46, "FreezeAssetAccount", TealType.bytes, False, 2)
    freeze_asset_frozen = (47, "FreezeAssetFrozen", TealType.uint64, False, 2)
    assets = (48, "Assets", TealType.uint64, True, 3)
    num_assets = (49, "NumAssets", TealType.uint64, False, 3)
    applications = (50, "Applications", TealType.uint64, True, 3)
    num_applications = (51, "NumApplications", TealType.uint64, False, 3)
    global_num_uints = (52, "GlobalNumUint", TealType.uint64, False, 3)
    global_num_byte_slices = (53, "GlobalNumByteSlice", TealType.uint64, False, 3)
    local_num_uints = (54, "LocalNumUint", TealType.uint64, False, 3)
    local_num_byte_slices = (55, "LocalNumByteSlice", TealType.uint64, False, 3)
    extra_program_pages = (56, "ExtraProgramPages", TealType.uint64, False, 4)
    nonparticipation = (57, "Nonparticipation", TealType.uint64, False, 5)
    logs = (58, "Logs", TealType.bytes, True, 5)
    num_logs = (59, "NumLogs", TealType.uint64, False, 5)
    created_asset_id = (60, "CreatedAssetID", TealType.uint64, False, 5)
    created_application_id = (61, "CreatedApplicationID", TealType.uint64, False, 5)
    last_log = (62, "LastLog", TealType.bytes, False, 6)
    state_proof_pk = (63, "StateProofPK", TealType.bytes, False, 6)
    approval_program_pages = (64, "ApprovalProgramPages", TealType.bytes, True, 7)
    num_approval_program_pages = (
        65,
        "NumApprovalProgramPages",
        TealType.uint64,
        False,
        7,
    )
    clear_state_program_pages = (66, "ClearStateProgramPages", TealType.bytes, True, 7)
    num_clear_state_program_pages = (
        67,
        "NumClearStateProgramPages",
        TealType.uint64,
        False,
        7,
    )

    def __init__(
        self, id: int, name: str, type: TealType, is_array: bool, min_version: int
    ) -> None:
        self.id = id
        self.arg_name = name
        self.ret_type = type
        self.is_array = is_array
        self.min_version = min_version

    def type_of(self) -> TealType:
        return self.ret_type


TxnField.__module__ = "pyteal"


class TxnExpr(LeafExpr):
    """An expression that accesses a transaction field from the current transaction."""

    def __init__(self, op: Op, name: str, field: TxnField) -> None:
        super().__init__()
        if field.is_array:
            raise TealInputError("Unexpected array field: {}".format(field))
        self.op = op
        self.name = name
        self.field = field

    def __str__(self):
        return "({} {})".format(self.name, self.field.arg_name)

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)
        verifyProgramVersion(
            self.op.min_version,
            options.version,
            "Program version too low to use op {}".format(self.op),
        )

        op = TealOp(self, self.op, self.field.arg_name)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return self.field.type_of()


TxnExpr.__module__ = "pyteal"


class TxnaExpr(LeafExpr):
    """An expression that accesses a transaction array field from the current transaction."""

    @staticmethod
    def __validate_index_or_throw(index: Union[int, Expr]):
        if not isinstance(index, (int, Expr)):
            raise TealInputError(
                f"Invalid index type:  Expected int or Expr, but received {index}."
            )
        if isinstance(index, Expr):
            require_type(index, TealType.uint64)

    def __init__(
        self,
        staticOp: Op,
        dynamicOp: Optional[Op],
        name: str,
        field: TxnField,
        index: Union[int, Expr],
    ) -> None:
        super().__init__()
        if not field.is_array:
            raise TealInputError("Unexpected non-array field: {}".format(field))
        self.__validate_index_or_throw(index)

        self.staticOp = staticOp
        self.dynamicOp = dynamicOp
        self.name = name
        self.field = field
        self.index = index

    def __str__(self):
        return "({} {} {})".format(self.name, self.field.arg_name, self.index)

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        opToUse = self.staticOp if type(self.index) is int else self.dynamicOp
        if opToUse is None:
            raise TealCompileError("Dynamic array indexing not supported", self)

        verifyProgramVersion(
            opToUse.min_version,
            options.version,
            "Program version too low to use op {}".format(opToUse),
        )

        if type(self.index) is int:
            op = TealOp(self, opToUse, self.field.arg_name, self.index)
            return TealBlock.FromOp(options, op)

        op = TealOp(self, opToUse, self.field.arg_name)
        return TealBlock.FromOp(options, op, cast(Expr, self.index))

    def type_of(self):
        return self.field.type_of()


TxnaExpr.__module__ = "pyteal"


class TxnExprBuilder:
    def __init__(self, op: Op, name: str):
        self.op = op
        self.name = name

    def __call__(self, field: TxnField) -> TxnExpr:
        return TxnExpr(self.op, self.name, field)


TxnExprBuilder.__module__ = "pyteal"


class TxnaExprBuilder:
    def __init__(self, staticOp: Op, dynamicOp: Optional[Op], name: str):
        self.staticOp = staticOp
        self.dynamicOp = dynamicOp
        self.name = name

    def __call__(self, field: TxnField, index: Union[int, Expr]) -> TxnaExpr:
        return TxnaExpr(self.staticOp, self.dynamicOp, self.name, field, index)


TxnaExprBuilder.__module__ = "pyteal"


class TxnArray(Array):
    """Represents a transaction array field."""

    def __init__(
        self, txnObject: "TxnObject", accessField: TxnField, lengthField: TxnField
    ) -> None:
        self.txnObject = txnObject
        self.accessField = accessField
        self.lengthField = lengthField

    def length(self) -> TxnExpr:
        return self.txnObject.makeTxnExpr(self.lengthField)

    def __getitem__(self, index: Union[int, Expr]) -> TxnaExpr:
        if type(index) is int:
            if index < 0:
                raise TealInputError("Invalid array index: {}".format(index))
        else:
            require_type(cast(Expr, index), TealType.uint64)

        return self.txnObject.makeTxnaExpr(self.accessField, index)


TxnArray.__module__ = "pyteal"


class TxnObject:
    """Represents a transaction and its fields."""

    def __init__(
        self,
        makeTxnExpr: Callable[[TxnField], TxnExpr],
        makeTxnaExpr: Callable[[TxnField, Union[int, Expr]], TxnaExpr],
    ) -> None:
        self.makeTxnExpr = makeTxnExpr
        self.makeTxnaExpr = makeTxnaExpr

    def sender(self) -> TxnExpr:
        """Get the 32 byte address of the sender.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#sender
        """
        return self.makeTxnExpr(TxnField.sender)

    def fee(self) -> TxnExpr:
        """Get the transaction fee in micro Algos.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#fee
        """
        return self.makeTxnExpr(TxnField.fee)

    def first_valid(self) -> TxnExpr:
        """Get the first valid round number.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#firstvalid
        """
        return self.makeTxnExpr(TxnField.first_valid)

    def first_valid_time(self) -> TxnExpr:
        """Get the UNIX timestamp of block before txn.FirstValid. Fails if negative.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#firstvalidtime
        """
        return self.makeTxnExpr(TxnField.first_valid_time)

    def last_valid(self) -> TxnExpr:
        """Get the last valid round number.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#lastvalid
        """
        return self.makeTxnExpr(TxnField.last_valid)

    def note(self) -> TxnExpr:
        """Get the transaction note.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#note
        """
        return self.makeTxnExpr(TxnField.note)

    def lease(self) -> TxnExpr:
        """Get the transaction lease.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#lease
        """
        return self.makeTxnExpr(TxnField.lease)

    def receiver(self) -> TxnExpr:
        """Get the 32 byte address of the receiver.

        Only set when :any:`type_enum()` is :any:`TxnType.Payment`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#receiver
        """
        return self.makeTxnExpr(TxnField.receiver)

    def amount(self) -> TxnExpr:
        """Get the amount of the transaction in micro Algos.

        Only set when :any:`type_enum()` is :any:`TxnType.Payment`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#amount
        """
        return self.makeTxnExpr(TxnField.amount)

    def close_remainder_to(self) -> TxnExpr:
        """Get the 32 byte address of the CloseRemainderTo field.

        Only set when :any:`type_enum()` is :any:`TxnType.Payment`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#closeremainderto
        """
        return self.makeTxnExpr(TxnField.close_remainder_to)

    def vote_pk(self) -> TxnExpr:
        """Get the root participation public key.

        Only set when :any:`type_enum()` is :any:`TxnType.KeyRegistration`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#votepk
        """
        return self.makeTxnExpr(TxnField.vote_pk)

    def selection_pk(self) -> TxnExpr:
        """Get the VRF public key.

        Only set when :any:`type_enum()` is :any:`TxnType.KeyRegistration`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#selectionpk
        """
        return self.makeTxnExpr(TxnField.selection_pk)

    def vote_first(self) -> TxnExpr:
        """Get the first round that the participation key is valid.

        Only set when :any:`type_enum()` is :any:`TxnType.KeyRegistration`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#votefirst
        """
        return self.makeTxnExpr(TxnField.vote_first)

    def vote_last(self) -> TxnExpr:
        """Get the last round that the participation key is valid.

        Only set when :any:`type_enum()` is :any:`TxnType.KeyRegistration`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#votelast
        """
        return self.makeTxnExpr(TxnField.vote_last)

    def vote_key_dilution(self) -> TxnExpr:
        """Get the dilution for the 2-level participation key.

        Only set when :any:`type_enum()` is :any:`TxnType.KeyRegistration`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#votekeydilution
        """
        return self.makeTxnExpr(TxnField.vote_key_dilution)

    def nonparticipation(self) -> TxnExpr:
        """Marks an account nonparticipating for rewards.

        Only set when :any:`type_enum()` is :any:`TxnType.KeyRegistration`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#nonparticipation

        Requires program version 5 or higher.
        """
        return self.makeTxnExpr(TxnField.nonparticipation)

    def type(self) -> TxnExpr:
        """Get the type of this transaction as a byte string.

        In most cases it is preferable to use :any:`type_enum()` instead.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#type
        """
        return self.makeTxnExpr(TxnField.type)

    def type_enum(self) -> TxnExpr:
        """Get the type of this transaction.

        See :any:`TxnType` for possible values.
        """
        return self.makeTxnExpr(TxnField.type_enum)

    def xfer_asset(self) -> TxnExpr:
        """Get the ID of the asset being transferred.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetTransfer`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#xferasset
        """
        return self.makeTxnExpr(TxnField.xfer_asset)

    def asset_amount(self) -> TxnExpr:
        """Get the amount of the asset being transferred, measured in the asset's units.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetTransfer`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#assetamount
        """
        return self.makeTxnExpr(TxnField.asset_amount)

    def asset_sender(self) -> TxnExpr:
        """Get the 32 byte address of the subject of clawback.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetTransfer`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#assetsender
        """
        return self.makeTxnExpr(TxnField.asset_sender)

    def asset_receiver(self) -> TxnExpr:
        """Get the recipient of the asset transfer.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetTransfer`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#assetreceiver
        """
        return self.makeTxnExpr(TxnField.asset_receiver)

    def asset_close_to(self) -> TxnExpr:
        """Get the closeout address of the asset transfer.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetTransfer`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#assetcloseto
        """
        return self.makeTxnExpr(TxnField.asset_close_to)

    def group_index(self) -> TxnExpr:
        """Get the position of the transaction within the atomic transaction group.

        A stand-alone transaction is implictly element 0 in a group of 1.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#group
        """
        return self.makeTxnExpr(TxnField.group_index)

    def tx_id(self) -> TxnExpr:
        """Get the 32 byte computed ID for the transaction."""
        return self.makeTxnExpr(TxnField.tx_id)

    def application_id(self) -> TxnExpr:
        """Get the application ID from the ApplicationCall portion of the current transaction.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall`.
        """
        return self.makeTxnExpr(TxnField.application_id)

    def on_completion(self) -> TxnExpr:
        """Get the on completion action from the ApplicationCall portion of the transaction.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall`.
        """
        return self.makeTxnExpr(TxnField.on_completion)

    def approval_program(self) -> TxnExpr:
        """Get the approval program.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall`.
        """
        return self.makeTxnExpr(TxnField.approval_program)

    def clear_state_program(self) -> TxnExpr:
        """Get the clear state program.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall`.
        """
        return self.makeTxnExpr(TxnField.clear_state_program)

    def rekey_to(self) -> TxnExpr:
        """Get the sender's new 32 byte AuthAddr.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#rekeyto
        """
        return self.makeTxnExpr(TxnField.rekey_to)

    def config_asset(self) -> TxnExpr:
        """Get the asset ID in asset config transaction.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#configasset
        """
        return self.makeTxnExpr(TxnField.config_asset)

    def config_asset_total(self) -> TxnExpr:
        """Get the total number of units of this asset created.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#total
        """
        return self.makeTxnExpr(TxnField.config_asset_total)

    def config_asset_decimals(self) -> TxnExpr:
        """Get the number of digits to display after the decimal place when displaying the asset.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#decimals
        """
        return self.makeTxnExpr(TxnField.config_asset_decimals)

    def config_asset_default_frozen(self) -> TxnExpr:
        """Check if the asset's slots are frozen by default or not.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#defaultfrozen
        """
        return self.makeTxnExpr(TxnField.config_asset_default_frozen)

    def config_asset_unit_name(self) -> TxnExpr:
        """Get the unit name of the asset.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#unitname
        """
        return self.makeTxnExpr(TxnField.config_asset_unit_name)

    def config_asset_name(self) -> TxnExpr:
        """Get the asset name.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#assetname
        """
        return self.makeTxnExpr(TxnField.config_asset_name)

    def config_asset_url(self) -> TxnExpr:
        """Get the asset URL.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#url
        """
        return self.makeTxnExpr(TxnField.config_asset_url)

    def config_asset_metadata_hash(self) -> TxnExpr:
        """Get the 32 byte commitment to some unspecified asset metdata.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#metadatahash
        """
        return self.makeTxnExpr(TxnField.config_asset_metadata_hash)

    def config_asset_manager(self) -> TxnExpr:
        """Get the 32 byte asset manager address.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#manageraddr
        """
        return self.makeTxnExpr(TxnField.config_asset_manager)

    def config_asset_reserve(self) -> TxnExpr:
        """Get the 32 byte asset reserve address.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#reserveaddr
        """
        return self.makeTxnExpr(TxnField.config_asset_reserve)

    def config_asset_freeze(self) -> TxnExpr:
        """Get the 32 byte asset freeze address.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#freezeaddr
        """
        return self.makeTxnExpr(TxnField.config_asset_freeze)

    def config_asset_clawback(self) -> TxnExpr:
        """Get the 32 byte asset clawback address.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#clawbackaddr
        """
        return self.makeTxnExpr(TxnField.config_asset_clawback)

    def created_asset_id(self) -> TxnExpr:
        """Get the asset ID allocated by the creation of an ASA.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetConfig` and this is an asset creation transaction.

        Requires program version 5 or higher.

        * v5 - Only works on inner transactions.
        * >= v6 - Works on top-level and inner transactions.
        """
        return self.makeTxnExpr(TxnField.created_asset_id)

    def freeze_asset(self) -> TxnExpr:
        """Get the asset ID being frozen or un-frozen.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetFreeze`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#freezeasset
        """
        return self.makeTxnExpr(TxnField.freeze_asset)

    def freeze_asset_account(self) -> TxnExpr:
        """Get the 32 byte address of the account whose asset slot is being frozen or un-frozen.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetFreeze`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#freezeaccount
        """
        return self.makeTxnExpr(TxnField.freeze_asset_account)

    def freeze_asset_frozen(self) -> TxnExpr:
        """Get the new frozen value for the asset.

        Only set when :any:`type_enum()` is :any:`TxnType.AssetFreeze`.

        For more information, see https://developer.algorand.org/docs/reference/transactions/#assetfrozen
        """
        return self.makeTxnExpr(TxnField.freeze_asset_frozen)

    def global_num_uints(self) -> TxnExpr:
        """Get the schema count of global state integers in an application creation call.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall` and this is an app creation call.

        Requires program version 3 or higher.
        """
        return self.makeTxnExpr(TxnField.global_num_uints)

    def global_num_byte_slices(self) -> TxnExpr:
        """Get the schema count of global state byte slices in an application creation call.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall` and this is an app creation call.

        Requires program version 3 or higher.
        """
        return self.makeTxnExpr(TxnField.global_num_byte_slices)

    def local_num_uints(self) -> TxnExpr:
        """Get the schema count of local state integers in an application creation call.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall` and this is an app creation call.

        Requires program version 3 or higher.
        """
        return self.makeTxnExpr(TxnField.local_num_uints)

    def local_num_byte_slices(self) -> TxnExpr:
        """Get the schema count of local state byte slices in an application creation call.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall` and this is an app creation call.

        Requires program version 3 or higher.
        """
        return self.makeTxnExpr(TxnField.local_num_byte_slices)

    def extra_program_pages(self) -> TxnExpr:
        """Get the number of additional pages for each of the application's approval and clear state programs.

        1 additional page means 2048 more total bytes, or 1024 for each program.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall` and this is an app creation call.

        Requires program version 4 or higher.
        """
        return self.makeTxnExpr(TxnField.extra_program_pages)

    def created_application_id(self) -> TxnExpr:
        """Get the application ID allocated by the creation of an application.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall` and this is an app creation call.

        Requires program version 5 or higher.

        * v5 - Only works on inner transactions.
        * >= v6 - Works on top-level and inner transactions.
        """
        return self.makeTxnExpr(TxnField.created_application_id)

    def last_log(self) -> TxnExpr:
        """A convenience method for getting the last logged message from a transaction.

        Only application calls may log a message. Returns an empty string if no messages were logged.

        Only set when :any:`type_enum()` is :any:`TxnType.ApplicationCall`.

        Requires program version 6 or higher.
        """
        return self.makeTxnExpr(TxnField.last_log)

    def state_proof_pk(self) -> TxnExpr:
        """Get the state proof public key commitment from a transaction.

        Requires program version 6 or higher.
        """
        return self.makeTxnExpr(TxnField.state_proof_pk)

    @property
    def application_args(self) -> TxnArray:
        """Application call arguments array.

        :type: TxnArray
        """
        return TxnArray(self, TxnField.application_args, TxnField.num_app_args)

    @property
    def accounts(self) -> TxnArray:
        """The accounts array in an ApplicationCall transaction.

        :type: TxnArray
        """
        return TxnArray(self, TxnField.accounts, TxnField.num_accounts)

    @property
    def assets(self) -> TxnArray:
        """The foreign asset array in an ApplicationCall transaction.

        :type: TxnArray

        Requires program version 3 or higher.
        """
        return TxnArray(self, TxnField.assets, TxnField.num_assets)

    @property
    def applications(self) -> TxnArray:
        """The applications array in an ApplicationCall transaction.

        :type: TxnArray

        Requires program version 3 or higher.
        """
        return TxnArray(self, TxnField.applications, TxnField.num_applications)

    @property
    def logs(self) -> TxnArray:
        """The log messages emitted by an application call.

        :type: TxnArray

        Requires program version 5 or higher.

        * v5 - Only works on inner transactions.
        * >= v6 - Works on top-level and inner transactions.
        """
        return TxnArray(self, TxnField.logs, TxnField.num_logs)

    @property
    def approval_program_pages(self) -> TxnArray:
        """The approval program pages.

        :type: TxnArray

        Requires program version 7 or higher.
        """
        return TxnArray(
            self, TxnField.approval_program_pages, TxnField.num_approval_program_pages
        )

    @property
    def clear_state_program_pages(self) -> TxnArray:
        """The clear state program pages.

        :type: TxnArray

        Requires program version 7 or higher.
        """
        return TxnArray(
            self,
            TxnField.clear_state_program_pages,
            TxnField.num_clear_state_program_pages,
        )


TxnObject.__module__ = "pyteal"

Txn: TxnObject = TxnObject(
    TxnExprBuilder(Op.txn, "Txn"), TxnaExprBuilder(Op.txna, Op.txnas, "Txna")
)

Txn.__module__ = "pyteal"
