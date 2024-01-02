import pytest

import pyteal as pt

avm2Options = pt.CompileOptions(version=2)
avm3Options = pt.CompileOptions(version=3)
avm5Options = pt.CompileOptions(version=5)
avm6Options = pt.CompileOptions(version=6)
avm9Options = pt.CompileOptions(version=9)
avm10Options = pt.CompileOptions(version=10)


def test_global_min_txn_fee():
    expr = pt.Global.min_txn_fee()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "MinTxnFee")])

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_min_balance():
    expr = pt.Global.min_balance()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "MinBalance")])

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_max_txn_life():
    expr = pt.Global.max_txn_life()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "MaxTxnLife")])

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_zero_address():
    expr = pt.Global.zero_address()
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "ZeroAddress")])

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_group_size():
    expr = pt.Global.group_size()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "GroupSize")])

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_logic_sig_version():
    expr = pt.Global.logic_sig_version()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "LogicSigVersion")])

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_round():
    expr = pt.Global.round()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "Round")])

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_latest_timestamp():
    expr = pt.Global.latest_timestamp()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "LatestTimestamp")])

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_current_application_id():
    expr = pt.Global.current_application_id()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.global_, "CurrentApplicationID")]
    )

    actual, _ = expr.__teal__(avm2Options)

    assert actual == expected


def test_global_creator_address():
    expr = pt.Global.creator_address()
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "CreatorAddress")])

    actual, _ = expr.__teal__(avm3Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm2Options)


def test_global_current_application_address():
    expr = pt.Global.current_application_address()
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.global_, "CurrentApplicationAddress")]
    )

    actual, _ = expr.__teal__(avm5Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_global_group_id():
    expr = pt.Global.group_id()
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "GroupID")])

    actual, _ = expr.__teal__(avm5Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_global_opcode_budget():
    expr = pt.Global.opcode_budget()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "OpcodeBudget")])

    actual, _ = expr.__teal__(avm6Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm5Options)


def test_global_caller_application_id():
    expr = pt.Global.caller_app_id()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.global_, "CallerApplicationID")]
    )

    actual, _ = expr.__teal__(avm6Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm5Options)


def test_global_caller_app_address():
    expr = pt.Global.caller_app_address()
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.global_, "CallerApplicationAddress")]
    )

    actual, _ = expr.__teal__(avm6Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm5Options)


def test_global_asset_create_min_balance():
    expr = pt.Global.asset_create_min_balance()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.global_, "AssetCreateMinBalance")]
    )

    actual, _ = expr.__teal__(avm10Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm9Options)


def test_global_asset_opt_in_min_balance():
    expr = pt.Global.asset_opt_in_min_balance()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.global_, "AssetOptInMinBalance")]
    )

    actual, _ = expr.__teal__(avm10Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm9Options)


def test_global_genesis_hash():
    expr = pt.Global.genesis_hash()
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.global_, "GenesisHash")])

    actual, _ = expr.__teal__(avm10Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm9Options)
