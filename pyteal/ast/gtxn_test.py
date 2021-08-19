import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import MAX_GROUP_SIZE, CompileOptions

GTXN_RANGE = range(MAX_GROUP_SIZE)

teal2Options = CompileOptions(version=2)
teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)


def test_gtxn_invalid():
    with pytest.raises(TealInputError):
        Gtxn[-1].fee()

    with pytest.raises(TealInputError):
        Gtxn[MAX_GROUP_SIZE + 1].sender()

    with pytest.raises(TealTypeError):
        Gtxn[Pop(Int(0))].sender()

    with pytest.raises(TealTypeError):
        Gtxn[Bytes("index")].sender()


def test_gtxn_dynamic_teal_2():
    with pytest.raises(TealInputError):
        Gtxn[Int(0)].sender().__teal__(teal2Options)


def test_gtxn_sender():
    for i in GTXN_RANGE:
        expr = Gtxn[i].sender()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "Sender")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_sender_dynamic():
    index = Int(0)
    expr = Gtxn[index].sender()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "Sender")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_fee():
    for i in GTXN_RANGE:
        expr = Gtxn[i].fee()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "Fee")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_fee_dynamic():
    index = Int(0)
    expr = Gtxn[index].fee()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "Fee")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_first_valid():
    for i in GTXN_RANGE:
        expr = Gtxn[i].first_valid()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "FirstValid")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_first_valid_dynamic():
    index = Int(0)
    expr = Gtxn[index].first_valid()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "FirstValid")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_last_valid():
    for i in GTXN_RANGE:
        expr = Gtxn[i].last_valid()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "LastValid")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_last_valid_dynamic():
    index = Int(0)
    expr = Gtxn[index].last_valid()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "LastValid")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_note():
    for i in GTXN_RANGE:
        expr = Gtxn[i].note()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "Note")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_note_dynamic():
    index = Int(0)
    expr = Gtxn[index].note()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "Note")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_lease():
    for i in GTXN_RANGE:
        expr = Gtxn[i].lease()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "Lease")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_lease_dynamic():
    index = Int(0)
    expr = Gtxn[index].lease()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "Lease")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_receiver():
    for i in GTXN_RANGE:
        expr = Gtxn[i].receiver()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "Receiver")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_receiver_dynamic():
    index = Int(0)
    expr = Gtxn[index].receiver()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "Receiver")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_amount():
    for i in GTXN_RANGE:
        expr = Gtxn[i].amount()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "Amount")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_amount_dynamic():
    index = Int(0)
    expr = Gtxn[index].amount()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "Amount")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_close_remainder_to():
    for i in GTXN_RANGE:
        expr = Gtxn[i].close_remainder_to()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "CloseRemainderTo")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_close_remainder_to_dynamic():
    index = Int(0)
    expr = Gtxn[index].close_remainder_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "CloseRemainderTo")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_vote_pk():
    for i in GTXN_RANGE:
        expr = Gtxn[i].vote_pk()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "VotePK")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_vote_pk_dynamic():
    index = Int(0)
    expr = Gtxn[index].vote_pk()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "VotePK")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_selection_pk():
    for i in GTXN_RANGE:
        expr = Gtxn[i].selection_pk()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "SelectionPK")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_selection_pk_dynamic():
    index = Int(0)
    expr = Gtxn[index].selection_pk()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "SelectionPK")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_vote_first():
    for i in GTXN_RANGE:
        expr = Gtxn[i].vote_first()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "VoteFirst")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_vote_first_dynamic():
    index = Int(0)
    expr = Gtxn[index].vote_first()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "VoteFirst")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_vote_last():
    for i in GTXN_RANGE:
        expr = Gtxn[i].vote_last()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "VoteLast")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_vote_last_dynamic():
    index = Int(0)
    expr = Gtxn[index].vote_last()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "VoteLast")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_vote_key_dilution():
    for i in GTXN_RANGE:
        expr = Gtxn[i].vote_key_dilution()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "VoteKeyDilution")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_vote_key_dilution_dynamic():
    index = Int(0)
    expr = Gtxn[index].vote_key_dilution()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "VoteKeyDilution")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_type():
    for i in GTXN_RANGE:
        expr = Gtxn[i].type()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "Type")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_type_dynamic():
    index = Int(0)
    expr = Gtxn[index].type()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "Type")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_type_enum():
    for i in GTXN_RANGE:
        expr = Gtxn[i].type_enum()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "TypeEnum")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_type_enum_dynamic():
    index = Int(0)
    expr = Gtxn[index].type_enum()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "TypeEnum")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_xfer_asset():
    for i in GTXN_RANGE:
        expr = Gtxn[i].xfer_asset()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "XferAsset")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_xfer_asset_dynamic():
    index = Int(0)
    expr = Gtxn[index].xfer_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "XferAsset")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_asset_amount():
    for i in GTXN_RANGE:
        expr = Gtxn[i].asset_amount()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "AssetAmount")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_asset_amount_dynamic():
    index = Int(0)
    expr = Gtxn[index].asset_amount()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "AssetAmount")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_asset_sender():
    for i in GTXN_RANGE:
        expr = Gtxn[i].asset_sender()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "AssetSender")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_asset_sender_dynamic():
    index = Int(0)
    expr = Gtxn[index].asset_sender()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "AssetSender")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_asset_receiver():
    for i in GTXN_RANGE:
        expr = Gtxn[i].asset_receiver()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "AssetReceiver")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_asset_receiver_dynamic():
    index = Int(0)
    expr = Gtxn[index].asset_receiver()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "AssetReceiver")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_asset_close_to():
    for i in GTXN_RANGE:
        expr = Gtxn[i].asset_close_to()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "AssetCloseTo")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_asset_close_to_dynamic():
    index = Int(0)
    expr = Gtxn[index].asset_close_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "AssetCloseTo")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_group_index():
    for i in GTXN_RANGE:
        expr = Gtxn[i].group_index()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "GroupIndex")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_group_index_dynamic():
    index = Int(0)
    expr = Gtxn[index].group_index()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "GroupIndex")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gtxn_id():
    for i in GTXN_RANGE:
        expr = Gtxn[i].tx_id()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "TxID")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_gtxn_id_dynamic():
    index = Int(0)
    expr = Gtxn[index].tx_id()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "TxID")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_application_id():
    for i in GTXN_RANGE:
        expr = Gtxn[i].application_id()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ApplicationID")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_application_id_dynamic():
    index = Int(0)
    expr = Gtxn[index].application_id()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ApplicationID")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_on_completion():
    for i in GTXN_RANGE:
        expr = Gtxn[i].on_completion()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "OnCompletion")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_on_completion_dynamic():
    index = Int(0)
    expr = Gtxn[index].on_completion()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "OnCompletion")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_application_args():
    for i in GTXN_RANGE:
        for j in range(32):
            expr = Gtxn[i].application_args[j]
            assert expr.type_of() == TealType.bytes

            expected = TealSimpleBlock(
                [TealOp(expr, Op.gtxna, i, "ApplicationArgs", j)]
            )

            actual, _ = expr.__teal__(teal2Options)

            assert actual == expected


def test_txn_application_args_dynamic():
    index = Int(0)
    for j in range(32):
        expr = Gtxn[index].application_args[j]
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock(
            [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxnsa, "ApplicationArgs", j)]
        )

        actual, _ = expr.__teal__(teal3Options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        assert actual == expected


def test_txn_application_args_length():
    for i in GTXN_RANGE:
        expr = Gtxn[i].application_args.length()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "NumAppArgs")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_application_args_length_dynamic():
    index = Int(0)
    expr = Gtxn[index].application_args.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "NumAppArgs")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_accounts():
    for i in GTXN_RANGE:
        for j in range(32):
            expr = Gtxn[i].accounts[j]
            assert expr.type_of() == TealType.bytes

            expected = TealSimpleBlock([TealOp(expr, Op.gtxna, i, "Accounts", j)])

            actual, _ = expr.__teal__(teal2Options)

            assert actual == expected


def test_txn_accounts_dynamic():
    index = Int(0)
    for j in range(32):
        expr = Gtxn[index].accounts[j]
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock(
            [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxnsa, "Accounts", j)]
        )

        actual, _ = expr.__teal__(teal3Options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        assert actual == expected


def test_txn_accounts_length():
    for i in GTXN_RANGE:
        expr = Gtxn[i].accounts.length()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "NumAccounts")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_accounts_length_dynamic():
    index = Int(0)
    expr = Gtxn[index].accounts.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "NumAccounts")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_approval_program():
    for i in GTXN_RANGE:
        expr = Gtxn[i].approval_program()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ApprovalProgram")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_approval_program_dynamic():
    index = Int(0)
    expr = Gtxn[index].approval_program()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ApprovalProgram")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_clear_state_program():
    for i in GTXN_RANGE:
        expr = Gtxn[i].clear_state_program()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ClearStateProgram")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_clear_state_program_dynamic():
    index = Int(0)
    expr = Gtxn[index].clear_state_program()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ClearStateProgram")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_rekey_to():
    for i in GTXN_RANGE:
        expr = Gtxn[i].rekey_to()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "RekeyTo")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_rekey_to_dynamic():
    index = Int(0)
    expr = Gtxn[index].rekey_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "RekeyTo")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAsset")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAsset")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_total():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_total()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetTotal")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_total_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_total()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetTotal")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_decimals():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_decimals()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetDecimals")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_decimals_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_decimals()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetDecimals")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_default_frozen():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_default_frozen()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock(
            [TealOp(expr, Op.gtxn, i, "ConfigAssetDefaultFrozen")]
        )

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_default_frozen_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_default_frozen()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetDefaultFrozen")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_unit_name():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_unit_name()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetUnitName")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_unit_name_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_unit_name()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetUnitName")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_name():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_name()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetName")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_name_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_name()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetName")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_url():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_url()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetURL")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_url_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_url()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetURL")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_metadata_hash():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_metadata_hash()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock(
            [TealOp(expr, Op.gtxn, i, "ConfigAssetMetadataHash")]
        )

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_metadata_hash_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_metadata_hash()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetMetadataHash")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_manager():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_manager()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetManager")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_manager_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_manager()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetManager")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_reserve():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_reserve()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetReserve")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_reserve_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_reserve()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetReserve")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_freeze():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_freeze()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetFreeze")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_freeze_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_freeze()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetFreeze")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_config_asset_clawback():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_clawback()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ConfigAssetClawback")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_config_asset_clawback_dynamic():
    index = Int(0)
    expr = Gtxn[index].config_asset_clawback()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ConfigAssetClawback")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_freeze_asset():
    for i in GTXN_RANGE:
        expr = Gtxn[i].freeze_asset()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "FreezeAsset")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_freeze_asset_dynamic():
    index = Int(0)
    expr = Gtxn[index].freeze_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "FreezeAsset")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_freeze_asset_account():
    for i in GTXN_RANGE:
        expr = Gtxn[i].freeze_asset_account()
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "FreezeAssetAccount")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_freeze_asset_account_dynamic():
    index = Int(0)
    expr = Gtxn[index].freeze_asset_account()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "FreezeAssetAccount")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_freeze_asset_frozen():
    for i in GTXN_RANGE:
        expr = Gtxn[i].freeze_asset_frozen()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "FreezeAssetFrozen")])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_freeze_asset_frozen_dynamic():
    index = Int(0)
    expr = Gtxn[index].freeze_asset_frozen()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "FreezeAssetFrozen")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_txn_assets():
    for i in GTXN_RANGE:
        for j in range(32):
            expr = Gtxn[i].assets[j]
            assert expr.type_of() == TealType.uint64

            expected = TealSimpleBlock([TealOp(expr, Op.gtxna, i, "Assets", j)])

            actual, _ = expr.__teal__(teal3Options)

            assert actual == expected

            with pytest.raises(TealInputError):
                expr.__teal__(teal2Options)


def test_txn_assets_dynamic():
    index = Int(0)
    for j in range(32):
        expr = Gtxn[index].assets[j]
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock(
            [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxnsa, "Assets", j)]
        )

        actual, _ = expr.__teal__(teal3Options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_assets_length():
    for i in GTXN_RANGE:
        expr = Gtxn[i].assets.length()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "NumAssets")])

        actual, _ = expr.__teal__(teal3Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_assets_length_dynamic():
    index = Int(0)
    expr = Gtxn[index].assets.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "NumAssets")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_applications():
    for i in GTXN_RANGE:
        for j in range(32):
            expr = Gtxn[i].applications[j]
            assert expr.type_of() == TealType.uint64

            expected = TealSimpleBlock([TealOp(expr, Op.gtxna, i, "Applications", j)])

            actual, _ = expr.__teal__(teal3Options)

            assert actual == expected

            with pytest.raises(TealInputError):
                expr.__teal__(teal2Options)


def test_txn_applications_dynamic():
    index = Int(0)
    for j in range(32):
        expr = Gtxn[index].applications[j]
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock(
            [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxnsa, "Applications", j)]
        )

        actual, _ = expr.__teal__(teal3Options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_applications_length():
    for i in GTXN_RANGE:
        expr = Gtxn[i].applications.length()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "NumApplications")])

        actual, _ = expr.__teal__(teal3Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_applications_length_dynamic():
    index = Int(0)
    expr = Gtxn[index].applications.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "NumApplications")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_global_num_uints():
    for i in GTXN_RANGE:
        expr = Gtxn[i].global_num_uints()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "GlobalNumUint")])

        actual, _ = expr.__teal__(teal3Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_global_num_uints_dynamic():
    index = Int(0)
    expr = Gtxn[index].global_num_uints()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "GlobalNumUint")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_global_num_byte_slices():
    for i in GTXN_RANGE:
        expr = Gtxn[i].global_num_byte_slices()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "GlobalNumByteSlice")])

        actual, _ = expr.__teal__(teal3Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_global_num_byte_slices_dynamic():
    index = Int(0)
    expr = Gtxn[index].global_num_byte_slices()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "GlobalNumByteSlice")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_local_num_uints():
    for i in GTXN_RANGE:
        expr = Gtxn[i].local_num_uints()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "LocalNumUint")])

        actual, _ = expr.__teal__(teal3Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_local_num_uints_dynamic():
    index = Int(0)
    expr = Gtxn[index].local_num_uints()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "LocalNumUint")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_local_num_byte_slices():
    for i in GTXN_RANGE:
        expr = Gtxn[i].local_num_byte_slices()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "LocalNumByteSlice")])

        actual, _ = expr.__teal__(teal3Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_local_num_byte_slices_dynamic():
    index = Int(0)
    expr = Gtxn[index].local_num_byte_slices()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "LocalNumByteSlice")]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_extra_program_pages():
    for i in GTXN_RANGE:
        expr = Gtxn[i].extra_program_pages()
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.gtxn, i, "ExtraProgramPages")])

        actual, _ = expr.__teal__(teal4Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal3Options)


def test_txn_extra_program_pages_dynamic():
    index = Int(0)
    expr = Gtxn[index].extra_program_pages()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(index, Op.int, 0), TealOp(expr, Op.gtxns, "ExtraProgramPages")]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)
