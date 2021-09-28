import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()
teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)


def test_on_complete():
    assert OnComplete.NoOp.__teal__(options)[0] == TealSimpleBlock(
        [TealOp(OnComplete.NoOp, Op.int, "NoOp")]
    )

    assert OnComplete.OptIn.__teal__(options)[0] == TealSimpleBlock(
        [TealOp(OnComplete.OptIn, Op.int, "OptIn")]
    )

    assert OnComplete.CloseOut.__teal__(options)[0] == TealSimpleBlock(
        [TealOp(OnComplete.CloseOut, Op.int, "CloseOut")]
    )

    assert OnComplete.ClearState.__teal__(options)[0] == TealSimpleBlock(
        [TealOp(OnComplete.ClearState, Op.int, "ClearState")]
    )

    assert OnComplete.UpdateApplication.__teal__(options)[0] == TealSimpleBlock(
        [TealOp(OnComplete.UpdateApplication, Op.int, "UpdateApplication")]
    )

    assert OnComplete.DeleteApplication.__teal__(options)[0] == TealSimpleBlock(
        [TealOp(OnComplete.DeleteApplication, Op.int, "DeleteApplication")]
    )


def test_app_id():
    expr = App.id()
    assert expr.type_of() == TealType.uint64
    with TealComponent.Context.ignoreExprEquality():
        assert (
            expr.__teal__(options)[0]
            == Global.current_application_id().__teal__(options)[0]
        )


def test_opted_in():
    args = [Int(1), Int(12)]
    expr = App.optedIn(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 12),
            TealOp(expr, Op.app_opted_in),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_opted_in_direct_ref():
    args = [Bytes("sender address"), Int(100)]
    expr = App.optedIn(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"sender address"'),
            TealOp(args[1], Op.int, 100),
            TealOp(expr, Op.app_opted_in),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_opted_in_invalid():
    with pytest.raises(TealTypeError):
        App.optedIn(Bytes("sender"), Bytes("100"))

    with pytest.raises(TealTypeError):
        App.optedIn(Int(123456), Bytes("364"))


def test_local_get():
    args = [Int(0), Bytes("key")]
    expr = App.localGet(args[0], args[1])
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 0),
            TealOp(args[1], Op.byte, '"key"'),
            TealOp(expr, Op.app_local_get),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_get_direct_ref():
    args = [Txn.sender(), Bytes("key")]
    expr = App.localGet(args[0], args[1])
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.txn, "Sender"),
            TealOp(args[1], Op.byte, '"key"'),
            TealOp(expr, Op.app_local_get),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_get_invalid():
    with pytest.raises(TealTypeError):
        App.localGet(Txn.sender(), Int(1337))

    with pytest.raises(TealTypeError):
        App.localGet(Int(0), Int(1))


def test_local_get_ex():
    args = [Int(0), Int(6), Bytes("key")]
    expr = App.localGetEx(args[0], args[1], args[2])
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.anytype

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 0),
            TealOp(args[1], Op.int, 6),
            TealOp(args[2], Op.byte, '"key"'),
            TealOp(expr, Op.app_local_get_ex),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_local_get_ex_direct_ref():
    args = [Txn.sender(), Int(6), Bytes("key")]
    expr = App.localGetEx(args[0], args[1], args[2])
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.anytype

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.txn, "Sender"),
            TealOp(args[1], Op.int, 6),
            TealOp(args[2], Op.byte, '"key"'),
            TealOp(expr, Op.app_local_get_ex),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_local_get_ex_invalid():
    with pytest.raises(TealTypeError):
        App.localGetEx(Txn.sender(), Int(0), Int(0x123456))

    with pytest.raises(TealTypeError):
        App.localGetEx(Int(0), Bytes("app"), Bytes("key"))


def test_global_get():
    arg = Bytes("key")
    expr = App.globalGet(arg)
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock(
        [TealOp(arg, Op.byte, '"key"'), TealOp(expr, Op.app_global_get)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_global_get_invalid():
    with pytest.raises(TealTypeError):
        App.globalGet(Int(7))


def test_global_get_ex():
    args = [Int(6), Bytes("key")]
    expr = App.globalGetEx(args[0], args[1])
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.anytype

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 6),
            TealOp(args[1], Op.byte, '"key"'),
            TealOp(expr, Op.app_global_get_ex),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_global_get_ex_direct_ref():
    args = [Txn.applications[0], Bytes("key")]
    expr = App.globalGetEx(args[0], args[1])
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.anytype

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.txna, "Applications", 0),
            TealOp(args[1], Op.byte, '"key"'),
            TealOp(expr, Op.app_global_get_ex),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_global_get_ex_invalid():
    with pytest.raises(TealTypeError):
        App.globalGetEx(Bytes("app"), Int(12))

    with pytest.raises(TealTypeError):
        App.globalGetEx(Int(0), Int(1))


def test_local_put():
    args = [Int(0), Bytes("key"), Int(5)]
    expr = App.localPut(args[0], args[1], args[2])
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 0),
            TealOp(args[1], Op.byte, '"key"'),
            TealOp(args[2], Op.int, 5),
            TealOp(expr, Op.app_local_put),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_put_direct_ref():
    args = [Txn.sender(), Bytes("key"), Int(5)]
    expr = App.localPut(args[0], args[1], args[2])
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.txn, "Sender"),
            TealOp(args[1], Op.byte, '"key"'),
            TealOp(args[2], Op.int, 5),
            TealOp(expr, Op.app_local_put),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_put_invalid():
    with pytest.raises(TealTypeError):
        App.localPut(Txn.sender(), Int(55), Int(5))

    with pytest.raises(TealTypeError):
        App.localPut(Int(1), Int(0), Int(5))

    with pytest.raises(TealTypeError):
        App.localPut(Int(1), Bytes("key"), Pop(Int(1)))


def test_global_put():
    args = [Bytes("key"), Int(5)]
    expr = App.globalPut(args[0], args[1])
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"key"'),
            TealOp(args[1], Op.int, 5),
            TealOp(expr, Op.app_global_put),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_global_put_invalid():
    with pytest.raises(TealTypeError):
        App.globalPut(Int(0), Int(5))

    with pytest.raises(TealTypeError):
        App.globalPut(Bytes("key"), Pop(Int(1)))


def test_local_del():
    args = [Int(0), Bytes("key")]
    expr = App.localDel(args[0], args[1])
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 0),
            TealOp(args[1], Op.byte, '"key"'),
            TealOp(expr, Op.app_local_del),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_del_direct_ref():
    args = [Txn.sender(), Bytes("key")]
    expr = App.localDel(args[0], args[1])
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.txn, "Sender"),
            TealOp(args[1], Op.byte, '"key"'),
            TealOp(expr, Op.app_local_del),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_del_invalid():
    with pytest.raises(TealTypeError):
        App.localDel(Txn.sender(), Int(123))

    with pytest.raises(TealTypeError):
        App.localDel(Int(1), Int(2))


def test_global_del():
    arg = Bytes("key")
    expr = App.globalDel(arg)
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock(
        [TealOp(arg, Op.byte, '"key"'), TealOp(expr, Op.app_global_del)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_global_del_invalid():
    with pytest.raises(TealTypeError):
        App.globalDel(Int(2))


def test_app_param_approval_program_valid():
    arg = Int(1)
    expr = AppParam.approvalProgram(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.app_params_get, "AppApprovalProgram"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_approval_program_invalid():
    with pytest.raises(TealTypeError):
        AppParam.approvalProgram(Txn.sender())


def test_app_param_clear_state_program_valid():
    arg = Int(0)
    expr = AppParam.clearStateProgram(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.app_params_get, "AppClearStateProgram"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_clear_state_program_invalid():
    with pytest.raises(TealTypeError):
        AppParam.clearStateProgram(Txn.sender())


def test_app_param_global_num_unit_valid():
    arg = Int(1)
    expr = AppParam.globalNumUnit(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.app_params_get, "AppGlobalNumUnit"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_global_num_unit_invalid():
    with pytest.raises(TealTypeError):
        AppParam.globalNumUnit(Txn.sender())


def test_app_param_global_num_byte_slice_valid():
    arg = Int(1)
    expr = AppParam.globalNumByteSlice(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.app_params_get, "AppGlobalNumByteSlice"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_global_num_byte_slice_invalid():
    with pytest.raises(TealTypeError):
        AppParam.globalNumByteSlice(Txn.sender())


def test_app_param_local_num_unit_valid():
    arg = Int(1)
    expr = AppParam.localNumUnit(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.app_params_get, "AppLocalNumUnit"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_local_num_unit_invalid():
    with pytest.raises(TealTypeError):
        AppParam.localNumUnit(Txn.sender())


def test_app_param_local_num_byte_slice_valid():
    arg = Int(1)
    expr = AppParam.localNumByteSlice(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.app_params_get, "AppLocalNumByteSlice"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_local_num_byte_slice_invalid():
    with pytest.raises(TealTypeError):
        AppParam.localNumByteSlice(Txn.sender())


def test_app_param_extra_programs_page_valid():
    arg = Int(1)
    expr = AppParam.extraProgramPages(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.app_params_get, "AppExtraProgramPages"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_extra_program_pages_invalid():
    with pytest.raises(TealTypeError):
        AppParam.extraProgramPages(Txn.sender())


def test_app_param_creator_valid():
    arg = Int(1)
    expr = AppParam.creator(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.app_params_get, "AppCreator"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_creator_invalid():
    with pytest.raises(TealTypeError):
        AppParam.creator(Txn.sender())


def test_app_param_address_valid():
    arg = Int(1)
    expr = AppParam.address(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.app_params_get, "AppAddress"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_address_invalid():
    with pytest.raises(TealTypeError):
        AppParam.address(Txn.sender())
