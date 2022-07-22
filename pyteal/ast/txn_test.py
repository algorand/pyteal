from typing import Dict, Callable

import pytest

import pyteal as pt

fieldToMethod: Dict[pt.TxnField, Callable[[pt.TxnObject], pt.Expr]] = {
    pt.TxnField.sender: lambda txn: txn.sender(),
    pt.TxnField.fee: lambda txn: txn.fee(),
    pt.TxnField.first_valid: lambda txn: txn.first_valid(),
    pt.TxnField.first_valid_time: lambda txn: txn.first_valid_time(),
    pt.TxnField.last_valid: lambda txn: txn.last_valid(),
    pt.TxnField.note: lambda txn: txn.note(),
    pt.TxnField.lease: lambda txn: txn.lease(),
    pt.TxnField.receiver: lambda txn: txn.receiver(),
    pt.TxnField.amount: lambda txn: txn.amount(),
    pt.TxnField.close_remainder_to: lambda txn: txn.close_remainder_to(),
    pt.TxnField.vote_pk: lambda txn: txn.vote_pk(),
    pt.TxnField.selection_pk: lambda txn: txn.selection_pk(),
    pt.TxnField.vote_first: lambda txn: txn.vote_first(),
    pt.TxnField.vote_last: lambda txn: txn.vote_last(),
    pt.TxnField.vote_key_dilution: lambda txn: txn.vote_key_dilution(),
    pt.TxnField.type: lambda txn: txn.type(),
    pt.TxnField.type_enum: lambda txn: txn.type_enum(),
    pt.TxnField.xfer_asset: lambda txn: txn.xfer_asset(),
    pt.TxnField.asset_amount: lambda txn: txn.asset_amount(),
    pt.TxnField.asset_sender: lambda txn: txn.asset_sender(),
    pt.TxnField.asset_receiver: lambda txn: txn.asset_receiver(),
    pt.TxnField.asset_close_to: lambda txn: txn.asset_close_to(),
    pt.TxnField.group_index: lambda txn: txn.group_index(),
    pt.TxnField.tx_id: lambda txn: txn.tx_id(),
    pt.TxnField.application_id: lambda txn: txn.application_id(),
    pt.TxnField.on_completion: lambda txn: txn.on_completion(),
    pt.TxnField.approval_program: lambda txn: txn.approval_program(),
    pt.TxnField.clear_state_program: lambda txn: txn.clear_state_program(),
    pt.TxnField.rekey_to: lambda txn: txn.rekey_to(),
    pt.TxnField.config_asset: lambda txn: txn.config_asset(),
    pt.TxnField.config_asset_total: lambda txn: txn.config_asset_total(),
    pt.TxnField.config_asset_decimals: lambda txn: txn.config_asset_decimals(),
    pt.TxnField.config_asset_default_frozen: lambda txn: txn.config_asset_default_frozen(),
    pt.TxnField.config_asset_unit_name: lambda txn: txn.config_asset_unit_name(),
    pt.TxnField.config_asset_name: lambda txn: txn.config_asset_name(),
    pt.TxnField.config_asset_url: lambda txn: txn.config_asset_url(),
    pt.TxnField.config_asset_metadata_hash: lambda txn: txn.config_asset_metadata_hash(),
    pt.TxnField.config_asset_manager: lambda txn: txn.config_asset_manager(),
    pt.TxnField.config_asset_reserve: lambda txn: txn.config_asset_reserve(),
    pt.TxnField.config_asset_freeze: lambda txn: txn.config_asset_freeze(),
    pt.TxnField.config_asset_clawback: lambda txn: txn.config_asset_clawback(),
    pt.TxnField.freeze_asset: lambda txn: txn.freeze_asset(),
    pt.TxnField.freeze_asset_account: lambda txn: txn.freeze_asset_account(),
    pt.TxnField.freeze_asset_frozen: lambda txn: txn.freeze_asset_frozen(),
    pt.TxnField.global_num_uints: lambda txn: txn.global_num_uints(),
    pt.TxnField.global_num_byte_slices: lambda txn: txn.global_num_byte_slices(),
    pt.TxnField.local_num_uints: lambda txn: txn.local_num_uints(),
    pt.TxnField.local_num_byte_slices: lambda txn: txn.local_num_byte_slices(),
    pt.TxnField.extra_program_pages: lambda txn: txn.extra_program_pages(),
    pt.TxnField.nonparticipation: lambda txn: txn.nonparticipation(),
    pt.TxnField.created_asset_id: lambda txn: txn.created_asset_id(),
    pt.TxnField.created_application_id: lambda txn: txn.created_application_id(),
    pt.TxnField.last_log: lambda txn: txn.last_log(),
    pt.TxnField.state_proof_pk: lambda txn: txn.state_proof_pk(),
}

arrayFieldToProperty: Dict[pt.TxnField, Callable[[pt.TxnObject], pt.TxnArray]] = {
    pt.TxnField.application_args: lambda txn: txn.application_args,
    pt.TxnField.accounts: lambda txn: txn.accounts,
    pt.TxnField.assets: lambda txn: txn.assets,
    pt.TxnField.applications: lambda txn: txn.applications,
    pt.TxnField.logs: lambda txn: txn.logs,
    pt.TxnField.approval_program_pages: lambda txn: txn.approval_program_pages,
    pt.TxnField.clear_state_program_pages: lambda txn: txn.clear_state_program_pages,
}

arrayFieldToLengthField: Dict[pt.TxnField, pt.TxnField] = {
    pt.TxnField.application_args: pt.TxnField.num_app_args,
    pt.TxnField.accounts: pt.TxnField.num_accounts,
    pt.TxnField.assets: pt.TxnField.num_assets,
    pt.TxnField.applications: pt.TxnField.num_applications,
    pt.TxnField.logs: pt.TxnField.num_logs,
    pt.TxnField.approval_program_pages: pt.TxnField.num_approval_program_pages,
    pt.TxnField.clear_state_program_pages: pt.TxnField.num_clear_state_program_pages,
}


def test_txn_fields():
    dynamicGtxnArg = pt.Int(0)

    txnObjects = [
        (pt.Txn, pt.Op.txn, pt.Op.txna, pt.Op.txnas, [], []),
        *[
            (pt.Gtxn[i], pt.Op.gtxn, pt.Op.gtxna, pt.Op.gtxnas, [i], [])
            for i in range(pt.MAX_GROUP_SIZE)
        ],
        (
            pt.Gtxn[dynamicGtxnArg],
            pt.Op.gtxns,
            pt.Op.gtxnsa,
            pt.Op.gtxnsas,
            [],
            [pt.TealOp(dynamicGtxnArg, pt.Op.int, 0)],
        ),
        (pt.InnerTxn, pt.Op.itxn, pt.Op.itxna, pt.Op.itxnas, [], []),
        *[
            (pt.Gitxn[i], pt.Op.gitxn, pt.Op.gitxna, pt.Op.gitxnas, [i], [])
            for i in range(pt.MAX_GROUP_SIZE)
        ],
    ]

    for (
        txnObject,
        op,
        staticArrayOp,
        dynamicArrayOp,
        immediateArgsPrefix,
        irPrefix,
    ) in txnObjects:
        for field in pt.TxnField:
            if field.is_array:
                array = arrayFieldToProperty[field](txnObject)
                lengthExpr = array.length()

                lengthFieldName = arrayFieldToLengthField[field].arg_name
                immediateArgs = immediateArgsPrefix + [lengthFieldName]
                expected = pt.TealSimpleBlock(
                    irPrefix + [pt.TealOp(lengthExpr, op, *immediateArgs)]
                )
                expected.addIncoming()
                expected = pt.TealBlock.NormalizeBlocks(expected)

                version = max(op.min_version, field.min_version)

                actual, _ = lengthExpr.__teal__(pt.CompileOptions(version=version))
                actual.addIncoming()
                actual = pt.TealBlock.NormalizeBlocks(actual)

                assert (
                    actual == expected
                ), "{}: array length for field {} does not match expected".format(
                    op, field
                )

                if version > 2:
                    with pytest.raises(pt.TealInputError):
                        lengthExpr.__teal__(pt.CompileOptions(version=version - 1))

                for i in range(32):  # just an arbitrary large int
                    elementExpr = array[i]

                    immediateArgs = immediateArgsPrefix + [field.arg_name, i]
                    expected = pt.TealSimpleBlock(
                        irPrefix
                        + [pt.TealOp(elementExpr, staticArrayOp, *immediateArgs)]
                    )
                    expected.addIncoming()
                    expected = pt.TealBlock.NormalizeBlocks(expected)

                    version = max(staticArrayOp.min_version, field.min_version)

                    actual, _ = elementExpr.__teal__(pt.CompileOptions(version=version))
                    actual.addIncoming()
                    actual = pt.TealBlock.NormalizeBlocks(actual)

                    assert (
                        actual == expected
                    ), "{}: static array field {} does not match expected".format(
                        staticArrayOp, field
                    )

                    if version > 2:
                        with pytest.raises(pt.TealInputError):
                            elementExpr.__teal__(pt.CompileOptions(version=version - 1))

                if dynamicArrayOp is not None:
                    dynamicIndex = pt.Int(2)
                    dynamicElementExpr = array[dynamicIndex]

                    immediateArgs = immediateArgsPrefix + [field.arg_name]
                    expected = pt.TealSimpleBlock(
                        irPrefix
                        + [
                            pt.TealOp(dynamicIndex, pt.Op.int, 2),
                            pt.TealOp(
                                dynamicElementExpr, dynamicArrayOp, *immediateArgs
                            ),
                        ]
                    )
                    expected.addIncoming()
                    expected = pt.TealBlock.NormalizeBlocks(expected)

                    version = max(dynamicArrayOp.min_version, field.min_version)

                    actual, _ = dynamicElementExpr.__teal__(
                        pt.CompileOptions(version=version)
                    )
                    actual.addIncoming()
                    actual = pt.TealBlock.NormalizeBlocks(actual)

                    assert (
                        actual == expected
                    ), "{}: dynamic array field {} does not match expected".format(
                        dynamicArrayOp, field
                    )

                    if version > 2:
                        with pytest.raises(pt.TealInputError):
                            dynamicElementExpr.__teal__(
                                pt.CompileOptions(version=version - 1)
                            )

                continue

            if field in arrayFieldToLengthField.values():
                # ignore length fields since they are checked with their arrays
                continue

            if field == pt.TxnField.first_valid_time:
                # ignore first_valid_time since it is not exposed on pt.TxnObject yet
                continue

            expr = fieldToMethod[field](txnObject)

            immediateArgs = immediateArgsPrefix + [field.arg_name]
            expected = pt.TealSimpleBlock(
                irPrefix + [pt.TealOp(expr, op, *immediateArgs)]
            )
            expected.addIncoming()
            expected = pt.TealBlock.NormalizeBlocks(expected)

            version = max(op.min_version, field.min_version)

            actual, _ = expr.__teal__(pt.CompileOptions(version=version))
            actual.addIncoming()
            actual = pt.TealBlock.NormalizeBlocks(actual)

            assert actual == expected, "{}: field {} does not match expected".format(
                op, field
            )

            if version > 2:
                with pytest.raises(pt.TealInputError):
                    expr.__teal__(pt.CompileOptions(version=version - 1))
