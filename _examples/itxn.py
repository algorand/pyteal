from pyteal import (
    AppParam,
    Assert,
    Bytes,
    Global,
    InnerTxnBuilder,
    Int,
    OnComplete,
    Seq,
    Subroutine,
    TealType,
    Txn,
    TxnField,
    TxnType,
)


@Subroutine(TealType.none)
def send_payment():

    return Seq(
        # example: ITXN_PAYMENT
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: Int(5000),
                TxnField.receiver: Txn.sender(),
            }
        ),
        InnerTxnBuilder.Submit(),
        # ...
        # The `Sender` for the above is implied to be Global.current_application_address().
        # If a different sender is needed, it'd have to be an account that has been rekeyed to
        # the application address.
        # example: ITXN_PAYMENT
    )


@Subroutine(TealType.none)
def send_asset():
    return Seq(
        # example: ITXN_ASSET_TRANSFER
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_amount: Int(5000),
                TxnField.asset_receiver: Txn.sender(),
                TxnField.xfer_asset: Txn.assets[0],
            }
        ),
        # ...
        InnerTxnBuilder.Submit(),
        # example: ITXN_ASSET_TRANSFER
    )


@Subroutine(TealType.none)
def asset_freeze():
    return Seq(
        # example: ITXN_ASSET_FREEZE
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetFreeze,
                TxnField.freeze_asset: Txn.assets[0],
                TxnField.freeze_asset_account: Txn.accounts[1],
                TxnField.freeze_asset_frozen: Int(1),
            }
        ),
        InnerTxnBuilder.Submit(),
        # ...
        # example: ITXN_ASSET_FREEZE
    )


@Subroutine(TealType.none)
def asset_revoke():
    return Seq(
        # example: ITXN_ASSET_REVOKE
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_receiver: Global.current_application_address(),
                # AssetSender is _only_ used in the case of clawback
                # Sender is implied to be current_application_address
                TxnField.asset_sender: Txn.accounts[1],
                TxnField.asset_amount: Int(1000),
            }
        ),
        InnerTxnBuilder.Submit(),
        # ...
        # example: ITXN_ASSET_REVOKE
    )


@Subroutine(TealType.none)
def asset_create():
    return Seq(
        # example: ITXN_ASSET_CREATE
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_total: Int(1000000),
                TxnField.config_asset_decimals: Int(3),
                TxnField.config_asset_unit_name: Bytes("oz"),
                TxnField.config_asset_name: Bytes("Gold"),
                TxnField.config_asset_url: Bytes("https://gold.rush"),
                TxnField.config_asset_manager: Global.current_application_address(),
                TxnField.config_asset_reserve: Global.current_application_address(),
                TxnField.config_asset_freeze: Global.current_application_address(),
                TxnField.config_asset_clawback: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),
        # ...
        # example: ITXN_ASSET_CREATE
    )


@Subroutine(TealType.none)
def asset_config():
    return Seq(
        # example: ITXN_ASSET_CONFIG
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset: Txn.assets[0],
                TxnField.config_asset_manager: Txn.sender(),
                TxnField.config_asset_reserve: Txn.sender(),
                TxnField.config_asset_freeze: Txn.sender(),
                TxnField.config_asset_clawback: Txn.sender(),
            }
        ),
        InnerTxnBuilder.Submit(),
        # ...
        # example: ITXN_ASSET_CONFIG
    )


@Subroutine(TealType.none)
def asset_destroy():
    return Seq(
        # example: ITXN_ASSET_DESTROY
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset: Txn.assets[0],
            }
        ),
        InnerTxnBuilder.Submit(),
        # ...
        # example: ITXN_ASSET_DESTROY
    )


@Subroutine(TealType.none)
def grouped_itxn():
    return Seq(
        # example: GROUPED_ITXN
        # This returns a `MaybeValue`, see pyteal docs
        addr := AppParam.address(Int(1234)),
        Assert(addr.hasValue()),
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: addr.value(),
                TxnField.amount: Int(1000000),
            }
        ),
        InnerTxnBuilder.Next(),  # This indicates we're moving to constructing the next txn in the group
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Int(1234),
                TxnField.on_completion: OnComplete.NoOp,
                # Note this is _not_ using the ABI to call the
                # method in the other app
                TxnField.application_args: [Bytes("buy")],
            }
        ),
        InnerTxnBuilder.Submit(),
        # ...
        # example: GROUPED_ITXN
    )


@Subroutine(TealType.none)
def inner_c2c():
    return Seq(
        # example: ITXN_C2C
        # ...
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Int(1234),
                TxnField.on_completion: OnComplete.NoOp,
            }
        ),
        InnerTxnBuilder.Submit(),
        # ...
        # example: ITXN_C2C
    )
