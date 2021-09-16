from typing import Dict, Callable

import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import Expr, TxnField, TxnObject, TxnArray, CompileOptions

fieldToMethod: Dict[TxnField, Callable[[TxnObject], Expr]] = {
    TxnField.sender: lambda txn: txn.sender(),
    TxnField.fee: lambda txn: txn.fee(),
    TxnField.first_valid: lambda txn: txn.first_valid(),
    TxnField.last_valid: lambda txn: txn.last_valid(),
    TxnField.note: lambda txn: txn.note(),
    TxnField.lease: lambda txn: txn.lease(),
    TxnField.receiver: lambda txn: txn.receiver(),
    TxnField.amount: lambda txn: txn.amount(),
    TxnField.close_remainder_to: lambda txn: txn.close_remainder_to(),
    TxnField.vote_pk: lambda txn: txn.vote_pk(),
    TxnField.selection_pk: lambda txn: txn.selection_pk(),
    TxnField.vote_first: lambda txn: txn.vote_first(),
    TxnField.vote_last: lambda txn: txn.vote_last(),
    TxnField.vote_key_dilution: lambda txn: txn.vote_key_dilution(),
    TxnField.type: lambda txn: txn.type(),
    TxnField.type_enum: lambda txn: txn.type_enum(),
    TxnField.xfer_asset: lambda txn: txn.xfer_asset(),
    TxnField.asset_amount: lambda txn: txn.asset_amount(),
    TxnField.asset_sender: lambda txn: txn.asset_sender(),
    TxnField.asset_receiver: lambda txn: txn.asset_receiver(),
    TxnField.asset_close_to: lambda txn: txn.asset_close_to(),
    TxnField.group_index: lambda txn: txn.group_index(),
    TxnField.tx_id: lambda txn: txn.tx_id(),
    TxnField.application_id: lambda txn: txn.application_id(),
    TxnField.on_completion: lambda txn: txn.on_completion(),
    TxnField.approval_program: lambda txn: txn.approval_program(),
    TxnField.clear_state_program: lambda txn: txn.clear_state_program(),
    TxnField.rekey_to: lambda txn: txn.rekey_to(),
    TxnField.config_asset: lambda txn: txn.config_asset(),
    TxnField.config_asset_total: lambda txn: txn.config_asset_total(),
    TxnField.config_asset_decimals: lambda txn: txn.config_asset_decimals(),
    TxnField.config_asset_default_frozen: lambda txn: txn.config_asset_default_frozen(),
    TxnField.config_asset_unit_name: lambda txn: txn.config_asset_unit_name(),
    TxnField.config_asset_name: lambda txn: txn.config_asset_name(),
    TxnField.config_asset_url: lambda txn: txn.config_asset_url(),
    TxnField.config_asset_metadata_hash: lambda txn: txn.config_asset_metadata_hash(),
    TxnField.config_asset_manager: lambda txn: txn.config_asset_manager(),
    TxnField.config_asset_reserve: lambda txn: txn.config_asset_reserve(),
    TxnField.config_asset_freeze: lambda txn: txn.config_asset_freeze(),
    TxnField.config_asset_clawback: lambda txn: txn.config_asset_clawback(),
    TxnField.freeze_asset: lambda txn: txn.freeze_asset(),
    TxnField.freeze_asset_account: lambda txn: txn.freeze_asset_account(),
    TxnField.freeze_asset_frozen: lambda txn: txn.freeze_asset_frozen(),
    TxnField.global_num_uints: lambda txn: txn.global_num_uints(),
    TxnField.global_num_byte_slices: lambda txn: txn.global_num_byte_slices(),
    TxnField.local_num_uints: lambda txn: txn.local_num_uints(),
    TxnField.local_num_byte_slices: lambda txn: txn.local_num_byte_slices(),
    TxnField.extra_program_pages: lambda txn: txn.extra_program_pages(),
    TxnField.nonparticipation: lambda txn: txn.nonparticipation(),
    TxnField.created_asset_id: lambda txn: txn.created_asset_id(),
    TxnField.created_application_id: lambda txn: txn.created_application_id(),
}

arrayFieldToProperty: Dict[TxnField, Callable[[TxnObject], TxnArray]] = {
    TxnField.application_args: lambda txn: txn.application_args,
    TxnField.accounts: lambda txn: txn.accounts,
    TxnField.assets: lambda txn: txn.assets,
    TxnField.applications: lambda txn: txn.applications,
    TxnField.logs: lambda txn: txn.logs,
}

arrayFieldToLengthField: Dict[TxnField, TxnField] = {
    TxnField.application_args: TxnField.num_app_args,
    TxnField.accounts: TxnField.num_accounts,
    TxnField.assets: TxnField.num_assets,
    TxnField.applications: TxnField.num_applications,
    TxnField.logs: TxnField.num_logs,
}


def test_txn_fields():
    dynamicGtxnArg = Int(0)

    txnObjects = [
        (Txn, Op.txn, Op.txna, Op.txnas, [], []),
        *[
            (Gtxn[i], Op.gtxn, Op.gtxna, Op.gtxnas, [i], [])
            for i in range(MAX_GROUP_SIZE)
        ],
        (
            Gtxn[dynamicGtxnArg],
            Op.gtxns,
            Op.gtxnsa,
            Op.gtxnsas,
            [],
            [TealOp(dynamicGtxnArg, Op.int, 0)],
        ),
        (InnerTxn, Op.itxn, Op.itxna, None, [], []),
    ]

    for (
        txnObject,
        op,
        staticArrayOp,
        dynamicArrayOp,
        immediateArgsPrefix,
        irPrefix,
    ) in txnObjects:
        for field in TxnField:
            if field.is_array:
                array = arrayFieldToProperty[field](txnObject)
                lengthExpr = array.length()

                lengthFieldName = arrayFieldToLengthField[field].arg_name
                immediateArgs = immediateArgsPrefix + [lengthFieldName]
                expected = TealSimpleBlock(
                    irPrefix + [TealOp(lengthExpr, op, *immediateArgs)]
                )
                expected.addIncoming()
                expected = TealBlock.NormalizeBlocks(expected)

                version = max(op.min_version, field.min_version)

                actual, _ = lengthExpr.__teal__(CompileOptions(version=version))
                actual.addIncoming()
                actual = TealBlock.NormalizeBlocks(actual)

                assert (
                    actual == expected
                ), "{}: array length for field {} does not match expected".format(
                    op, field
                )

                if version > 2:
                    with pytest.raises(TealInputError):
                        lengthExpr.__teal__(CompileOptions(version=version - 1))

                for i in range(32):  # just an arbitrary large int
                    elementExpr = array[i]

                    immediateArgs = immediateArgsPrefix + [field.arg_name, i]
                    expected = TealSimpleBlock(
                        irPrefix + [TealOp(elementExpr, staticArrayOp, *immediateArgs)]
                    )
                    expected.addIncoming()
                    expected = TealBlock.NormalizeBlocks(expected)

                    version = max(staticArrayOp.min_version, field.min_version)

                    actual, _ = elementExpr.__teal__(CompileOptions(version=version))
                    actual.addIncoming()
                    actual = TealBlock.NormalizeBlocks(actual)

                    assert (
                        actual == expected
                    ), "{}: static array field {} does not match expected".format(
                        staticArrayOp, field
                    )

                    if version > 2:
                        with pytest.raises(TealInputError):
                            elementExpr.__teal__(CompileOptions(version=version - 1))

                if dynamicArrayOp is not None:
                    dynamicIndex = Int(2)
                    dynamicElementExpr = array[dynamicIndex]

                    immediateArgs = immediateArgsPrefix + [field.arg_name]
                    expected = TealSimpleBlock(
                        irPrefix
                        + [
                            TealOp(dynamicIndex, Op.int, 2),
                            TealOp(dynamicElementExpr, dynamicArrayOp, *immediateArgs),
                        ]
                    )
                    expected.addIncoming()
                    expected = TealBlock.NormalizeBlocks(expected)

                    version = max(dynamicArrayOp.min_version, field.min_version)

                    actual, _ = dynamicElementExpr.__teal__(
                        CompileOptions(version=version)
                    )
                    actual.addIncoming()
                    actual = TealBlock.NormalizeBlocks(actual)

                    assert (
                        actual == expected
                    ), "{}: dynamic array field {} does not match expected".format(
                        dynamicArrayOp, field
                    )

                    if version > 2:
                        with pytest.raises(TealInputError):
                            dynamicElementExpr.__teal__(
                                CompileOptions(version=version - 1)
                            )

                continue

            if field in arrayFieldToLengthField.values():
                # ignore length fields since they are checked with their arrays
                continue

            if field == TxnField.first_valid_time:
                # ignore first_valid_time since it is not exposed on TxnObject yet
                continue

            expr = fieldToMethod[field](txnObject)

            immediateArgs = immediateArgsPrefix + [field.arg_name]
            expected = TealSimpleBlock(irPrefix + [TealOp(expr, op, *immediateArgs)])
            expected.addIncoming()
            expected = TealBlock.NormalizeBlocks(expected)

            version = max(op.min_version, field.min_version)

            actual, _ = expr.__teal__(CompileOptions(version=version))
            actual.addIncoming()
            actual = TealBlock.NormalizeBlocks(actual)

            assert actual == expected, "{}: field {} does not match expected".format(
                op, field
            )

            if version > 2:
                with pytest.raises(TealInputError):
                    expr.__teal__(CompileOptions(version=version - 1))
