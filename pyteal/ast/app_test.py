import pytest

from .. import *

def test_on_complete():
    assert OnComplete.NoOp.__teal__() == [
        TealOp(Op.int, "NoOp")
    ]

    assert OnComplete.OptIn.__teal__() == [
        TealOp(Op.int, "OptIn")
    ]

    assert OnComplete.CloseOut.__teal__() == [
        TealOp(Op.int, "CloseOut")
    ]

    assert OnComplete.ClearState.__teal__() == [
        TealOp(Op.int, "ClearState")
    ]

    assert OnComplete.UpdateApplication.__teal__() == [
        TealOp(Op.int, "UpdateApplication")
    ]

    assert OnComplete.DeleteApplication.__teal__() == [
        TealOp(Op.int, "DeleteApplication")
    ]

def test_app_id():
    expr = App.id()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == Global.current_application_id().__teal__()

def test_opted_in():
    expr = App.optedIn(Int(1), Int(12))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 12),
        TealOp(Op.app_opted_in)
    ]

def test_local_get():
    expr = App.localGet(Int(0), Bytes("key"))
    assert expr.type_of() == TealType.anytype
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.app_local_get)
    ]

def test_local_get_invalid():
    with pytest.raises(TealTypeError):
        App.localGet(Txn.sender(), Bytes("key"))
    
    with pytest.raises(TealTypeError):
        App.localGet(Int(0), Int(1))

def test_local_get_ex():
    expr = App.localGetEx(Int(0), Int(6), Bytes("key"))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.anytype
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.int, 6),
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.app_local_get_ex),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_local_get_ex_invalid():
    with pytest.raises(TealTypeError):
        App.localGetEx(Txn.sender(), Int(0), Bytes("key"))
    
    with pytest.raises(TealTypeError):
        App.localGetEx(Int(0), Bytes("app"), Bytes("key"))

    with pytest.raises(TealTypeError):
        App.localGetEx(Int(0), Int(0), Int(1))

def test_global_get():
    expr = App.globalGet(Bytes("key"))
    assert expr.type_of() == TealType.anytype
    assert expr.__teal__() == [
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.app_global_get)
    ]

def test_global_get_invalid():
    with pytest.raises(TealTypeError):
        App.globalGet(Int(7))

def test_global_get_ex():
    expr = App.globalGetEx(Int(6), Bytes("key"))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.anytype
    assert expr.__teal__() == [
        TealOp(Op.int, 6),
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.app_global_get_ex),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_global_get_ex_invalid():
    with pytest.raises(TealTypeError):
        App.globalGetEx(Bytes("app"), Bytes("key"))

    with pytest.raises(TealTypeError):
        App.globalGetEx(Int(0), Int(1))

def test_local_put():
    expr = App.localPut(Int(0), Bytes("key"), Int(5))
    assert expr.type_of() == TealType.none
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.int, 5),
        TealOp(Op.app_local_put)
    ]

def test_local_put_invalid():
    with pytest.raises(TealTypeError):
        App.localPut(Txn.sender(), Bytes("key"), Int(5))
    
    with pytest.raises(TealTypeError):
        App.localPut(Int(1), Int(0), Int(5))
    
    with pytest.raises(TealTypeError):
        App.localPut(Int(1), Bytes("key"), Pop(Int(1)))

def test_global_put():
    expr = App.globalPut(Bytes("key"), Int(5))
    assert expr.type_of() == TealType.none
    assert expr.__teal__() == [
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.int, 5),
        TealOp(Op.app_global_put)
    ]

def test_global_put_invalid():
    with pytest.raises(TealTypeError):
        App.globalPut(Int(0), Int(5))
    
    with pytest.raises(TealTypeError):
        App.globalPut(Bytes("key"), Pop(Int(1)))

def test_local_del():
    expr = App.localDel(Int(0), Bytes("key"))
    assert expr.type_of() == TealType.none
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.app_local_del)
    ]

def test_local_del_invalid():
    with pytest.raises(TealTypeError):
        App.localDel(Txn.sender(), Bytes("key"))
    
    with pytest.raises(TealTypeError):
        App.localDel(Int(1), Int(2))

def test_global_del():
    expr = App.globalDel(Bytes("key"))
    assert expr.type_of() == TealType.none
    assert expr.__teal__() == [
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.app_global_del)
    ]

def test_global_del_invalid():
    with pytest.raises(TealTypeError):
        App.globalDel(Int(2))
