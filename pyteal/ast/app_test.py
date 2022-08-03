import pytest

import pyteal as pt
from pyteal.ast.maybe_test import assert_MaybeValue_equality

options = pt.CompileOptions()
avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)


def test_on_complete():
    assert pt.OnComplete.NoOp.__teal__(options)[0] == pt.TealSimpleBlock(
        [pt.TealOp(pt.OnComplete.NoOp, pt.Op.int, "NoOp")]
    )

    assert pt.OnComplete.OptIn.__teal__(options)[0] == pt.TealSimpleBlock(
        [pt.TealOp(pt.OnComplete.OptIn, pt.Op.int, "OptIn")]
    )

    assert pt.OnComplete.CloseOut.__teal__(options)[0] == pt.TealSimpleBlock(
        [pt.TealOp(pt.OnComplete.CloseOut, pt.Op.int, "CloseOut")]
    )

    assert pt.OnComplete.ClearState.__teal__(options)[0] == pt.TealSimpleBlock(
        [pt.TealOp(pt.OnComplete.ClearState, pt.Op.int, "ClearState")]
    )

    assert pt.OnComplete.UpdateApplication.__teal__(options)[0] == pt.TealSimpleBlock(
        [pt.TealOp(pt.OnComplete.UpdateApplication, pt.Op.int, "UpdateApplication")]
    )

    assert pt.OnComplete.DeleteApplication.__teal__(options)[0] == pt.TealSimpleBlock(
        [pt.TealOp(pt.OnComplete.DeleteApplication, pt.Op.int, "DeleteApplication")]
    )


def test_app_id():
    expr = pt.App.id()
    assert expr.type_of() == pt.TealType.uint64
    with pt.TealComponent.Context.ignoreExprEquality():
        assert (
            expr.__teal__(options)[0]
            == pt.Global.current_application_id().__teal__(options)[0]
        )


def test_opted_in():
    args = [pt.Int(1), pt.Int(12)]
    expr = pt.App.optedIn(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 12),
            pt.TealOp(expr, pt.Op.app_opted_in),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_opted_in_direct_ref():
    args = [pt.Bytes("sender address"), pt.Int(100)]
    expr = pt.App.optedIn(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"sender address"'),
            pt.TealOp(args[1], pt.Op.int, 100),
            pt.TealOp(expr, pt.Op.app_opted_in),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_opted_in_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.optedIn(pt.Bytes("sender"), pt.Bytes("100"))

    with pytest.raises(pt.TealTypeError):
        pt.App.optedIn(pt.Int(123456), pt.Bytes("364"))


def test_local_get():
    args = [pt.Int(0), pt.Bytes("key")]
    expr = pt.App.localGet(args[0], args[1])
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 0),
            pt.TealOp(args[1], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.app_local_get),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_get_direct_ref():
    args = [pt.Txn.sender(), pt.Bytes("key")]
    expr = pt.App.localGet(args[0], args[1])
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.txn, "Sender"),
            pt.TealOp(args[1], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.app_local_get),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_get_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.localGet(pt.Txn.sender(), pt.Int(1337))

    with pytest.raises(pt.TealTypeError):
        pt.App.localGet(pt.Int(0), pt.Int(1))


def test_local_get_ex():
    args = [pt.Int(0), pt.Int(6), pt.Bytes("key")]
    expr = pt.App.localGetEx(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 0),
            pt.TealOp(args[1], pt.Op.int, 6),
            pt.TealOp(args[2], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.app_local_get_ex),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_local_get_ex_direct_ref():
    args = [pt.Txn.sender(), pt.Int(6), pt.Bytes("key")]
    expr = pt.App.localGetEx(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.txn, "Sender"),
            pt.TealOp(args[1], pt.Op.int, 6),
            pt.TealOp(args[2], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.app_local_get_ex),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_local_get_ex_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.localGetEx(pt.Txn.sender(), pt.Int(0), pt.Int(0x123456))

    with pytest.raises(pt.TealTypeError):
        pt.App.localGetEx(pt.Int(0), pt.Bytes("app"), pt.Bytes("key"))


def test_global_get():
    arg = pt.Bytes("key")
    expr = pt.App.globalGet(arg)
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.byte, '"key"'), pt.TealOp(expr, pt.Op.app_global_get)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_global_get_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.globalGet(pt.Int(7))


def test_global_get_ex():
    args = [pt.Int(6), pt.Bytes("key")]
    expr = pt.App.globalGetEx(args[0], args[1])
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 6),
            pt.TealOp(args[1], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.app_global_get_ex),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_global_get_ex_direct_ref():
    args = [pt.Txn.applications[0], pt.Bytes("key")]
    expr = pt.App.globalGetEx(args[0], args[1])
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.txna, "Applications", 0),
            pt.TealOp(args[1], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.app_global_get_ex),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_global_get_ex_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.globalGetEx(pt.Bytes("app"), pt.Int(12))

    with pytest.raises(pt.TealTypeError):
        pt.App.globalGetEx(pt.Int(0), pt.Int(1))


def test_local_put():
    args = [pt.Int(0), pt.Bytes("key"), pt.Int(5)]
    expr = pt.App.localPut(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 0),
            pt.TealOp(args[1], pt.Op.byte, '"key"'),
            pt.TealOp(args[2], pt.Op.int, 5),
            pt.TealOp(expr, pt.Op.app_local_put),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_put_direct_ref():
    args = [pt.Txn.sender(), pt.Bytes("key"), pt.Int(5)]
    expr = pt.App.localPut(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.txn, "Sender"),
            pt.TealOp(args[1], pt.Op.byte, '"key"'),
            pt.TealOp(args[2], pt.Op.int, 5),
            pt.TealOp(expr, pt.Op.app_local_put),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_put_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.localPut(pt.Txn.sender(), pt.Int(55), pt.Int(5))

    with pytest.raises(pt.TealTypeError):
        pt.App.localPut(pt.Int(1), pt.Int(0), pt.Int(5))

    with pytest.raises(pt.TealTypeError):
        pt.App.localPut(pt.Int(1), pt.Bytes("key"), pt.Pop(pt.Int(1)))


def test_global_put():
    args = [pt.Bytes("key"), pt.Int(5)]
    expr = pt.App.globalPut(args[0], args[1])
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"key"'),
            pt.TealOp(args[1], pt.Op.int, 5),
            pt.TealOp(expr, pt.Op.app_global_put),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_global_put_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.globalPut(pt.Int(0), pt.Int(5))

    with pytest.raises(pt.TealTypeError):
        pt.App.globalPut(pt.Bytes("key"), pt.Pop(pt.Int(1)))


def test_local_del():
    args = [pt.Int(0), pt.Bytes("key")]
    expr = pt.App.localDel(args[0], args[1])
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 0),
            pt.TealOp(args[1], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.app_local_del),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_del_direct_ref():
    args = [pt.Txn.sender(), pt.Bytes("key")]
    expr = pt.App.localDel(args[0], args[1])
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.txn, "Sender"),
            pt.TealOp(args[1], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.app_local_del),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_local_del_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.localDel(pt.Txn.sender(), pt.Int(123))

    with pytest.raises(pt.TealTypeError):
        pt.App.localDel(pt.Int(1), pt.Int(2))


def test_global_del():
    arg = pt.Bytes("key")
    expr = pt.App.globalDel(arg)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.byte, '"key"'), pt.TealOp(expr, pt.Op.app_global_del)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_global_del_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.App.globalDel(pt.Int(2))


def test_app_param_approval_program_valid():
    arg = pt.Int(1)
    expr = pt.AppParam.approvalProgram(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.app_params_get, "AppApprovalProgram"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_approval_program_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.approvalProgram(pt.Txn.sender())


def test_app_param_clear_state_program_valid():
    arg = pt.Int(0)
    expr = pt.AppParam.clearStateProgram(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.app_params_get, "AppClearStateProgram"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_clear_state_program_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.clearStateProgram(pt.Txn.sender())


def test_app_param_global_num_uint_valid():
    arg = pt.Int(1)
    expr = pt.AppParam.globalNumUint(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.app_params_get, "AppGlobalNumUint"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_global_num_uint_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.globalNumUint(pt.Txn.sender())


def test_app_param_global_num_byte_slice_valid():
    arg = pt.Int(1)
    expr = pt.AppParam.globalNumByteSlice(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.app_params_get, "AppGlobalNumByteSlice"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_global_num_byte_slice_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.globalNumByteSlice(pt.Txn.sender())


def test_app_param_local_num_uint_valid():
    arg = pt.Int(1)
    expr = pt.AppParam.localNumUint(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.app_params_get, "AppLocalNumUint"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_local_num_uint_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.localNumUint(pt.Txn.sender())


def test_app_param_local_num_byte_slice_valid():
    arg = pt.Int(1)
    expr = pt.AppParam.localNumByteSlice(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.app_params_get, "AppLocalNumByteSlice"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_local_num_byte_slice_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.localNumByteSlice(pt.Txn.sender())


def test_app_param_extra_programs_page_valid():
    arg = pt.Int(1)
    expr = pt.AppParam.extraProgramPages(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.app_params_get, "AppExtraProgramPages"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_extra_program_pages_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.extraProgramPages(pt.Txn.sender())


def test_app_param_creator_valid():
    arg = pt.Int(1)
    expr = pt.AppParam.creator(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.app_params_get, "AppCreator"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_creator_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.creator(pt.Txn.sender())


def test_app_param_address_valid():
    arg = pt.Int(1)
    expr = pt.AppParam.address(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.app_params_get, "AppAddress"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_app_param_address_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AppParam.address(pt.Txn.sender())


def test_AppParamObject():
    for app in (pt.Int(1), pt.Int(100)):
        obj = pt.AppParamObject(app)

        assert obj._app is app

        assert_MaybeValue_equality(
            obj.approval_program(), pt.AppParam.approvalProgram(app), avm5Options
        )
        assert_MaybeValue_equality(
            obj.clear_state_program(), pt.AppParam.clearStateProgram(app), avm5Options
        )
        assert_MaybeValue_equality(
            obj.global_num_uint(), pt.AppParam.globalNumUint(app), avm5Options
        )
        assert_MaybeValue_equality(
            obj.global_num_byte_slice(),
            pt.AppParam.globalNumByteSlice(app),
            avm5Options,
        )
        assert_MaybeValue_equality(
            obj.local_num_uint(), pt.AppParam.localNumUint(app), avm5Options
        )
        assert_MaybeValue_equality(
            obj.local_num_byte_slice(), pt.AppParam.localNumByteSlice(app), avm5Options
        )
        assert_MaybeValue_equality(
            obj.extra_program_pages(), pt.AppParam.extraProgramPages(app), avm5Options
        )
        assert_MaybeValue_equality(
            obj.creator_address(), pt.AppParam.creator(app), avm5Options
        )
        assert_MaybeValue_equality(obj.address(), pt.AppParam.address(app), avm5Options)
