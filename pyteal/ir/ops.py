from typing import NamedTuple
from enum import Enum, Flag, auto

class Mode(Flag):
    """Enum of program running modes."""
    
    Signature = auto()
    Application = auto()

Mode.__module__ = "pyteal"

OpType = NamedTuple('OpType', [('value', str), ('mode', Mode), ('min_version', int)])

class Op(Enum):
    """Enum of program opcodes."""

    def __str__(self) -> str:
        return self.value.value

    @property
    def mode(self) -> Mode:
        """Get the modes where this op is available."""
        return self.value.mode

    @property
    def min_version(self) -> int:
        """Get the minimum version where this op is available."""
        return self.value.min_version

    err               = OpType("err",               Mode.Signature | Mode.Application, 2)
    sha256            = OpType("sha256",            Mode.Signature | Mode.Application, 2)
    keccak256         = OpType("keccak256",         Mode.Signature | Mode.Application, 2)
    sha512_256        = OpType("sha512_256",        Mode.Signature | Mode.Application, 2)
    ed25519verify     = OpType("ed25519verify",     Mode.Signature,                    2)
    add               = OpType("+",                 Mode.Signature | Mode.Application, 2)
    minus             = OpType("-",                 Mode.Signature | Mode.Application, 2)
    div               = OpType("/",                 Mode.Signature | Mode.Application, 2)
    mul               = OpType("*",                 Mode.Signature | Mode.Application, 2)
    lt                = OpType("<",                 Mode.Signature | Mode.Application, 2)
    gt                = OpType(">",                 Mode.Signature | Mode.Application, 2)
    le                = OpType("<=",                Mode.Signature | Mode.Application, 2)
    ge                = OpType(">=",                Mode.Signature | Mode.Application, 2)
    logic_and         = OpType("&&",                Mode.Signature | Mode.Application, 2)
    logic_or          = OpType("||",                Mode.Signature | Mode.Application, 2)
    eq                = OpType("==",                Mode.Signature | Mode.Application, 2)
    neq               = OpType("!=",                Mode.Signature | Mode.Application, 2)
    logic_not         = OpType("!",                 Mode.Signature | Mode.Application, 2)
    len               = OpType("len",               Mode.Signature | Mode.Application, 2)
    itob              = OpType("itob",              Mode.Signature | Mode.Application, 2)
    btoi              = OpType("btoi",              Mode.Signature | Mode.Application, 2)
    mod               = OpType("%",                 Mode.Signature | Mode.Application, 2)
    bitwise_or        = OpType("|",                 Mode.Signature | Mode.Application, 2)
    bitwise_and       = OpType("&",                 Mode.Signature | Mode.Application, 2)
    bitwise_xor       = OpType("^",                 Mode.Signature | Mode.Application, 2)
    bitwise_not       = OpType("~",                 Mode.Signature | Mode.Application, 2)
    mulw              = OpType("mulw",              Mode.Signature | Mode.Application, 2)
    addw              = OpType("addw",              Mode.Signature | Mode.Application, 2)
    int               = OpType("int",               Mode.Signature | Mode.Application, 2)
    byte              = OpType("byte",              Mode.Signature | Mode.Application, 2)
    addr              = OpType("addr",              Mode.Signature | Mode.Application, 2)
    arg               = OpType("arg",               Mode.Signature,                    2)
    txn               = OpType("txn",               Mode.Signature | Mode.Application, 2)
    global_           = OpType("global",            Mode.Signature | Mode.Application, 2)
    gtxn              = OpType("gtxn",              Mode.Signature | Mode.Application, 2)
    load              = OpType("load",              Mode.Signature | Mode.Application, 2)
    store             = OpType("store",             Mode.Signature | Mode.Application, 2)
    txna              = OpType("txna",              Mode.Signature | Mode.Application, 2)
    gtxna             = OpType("gtxna",             Mode.Signature | Mode.Application, 2)
    bnz               = OpType("bnz",               Mode.Signature | Mode.Application, 2)
    bz                = OpType("bz",                Mode.Signature | Mode.Application, 2)
    b                 = OpType("b",                 Mode.Signature | Mode.Application, 2)
    return_           = OpType("return",            Mode.Signature | Mode.Application, 2)
    pop               = OpType("pop",               Mode.Signature | Mode.Application, 2)
    dup               = OpType("dup",               Mode.Signature | Mode.Application, 2)
    dup2              = OpType("dup2",              Mode.Signature | Mode.Application, 2)
    concat            = OpType("concat",            Mode.Signature | Mode.Application, 2)
    substring         = OpType("substring",         Mode.Signature | Mode.Application, 2)
    substring3        = OpType("substring3",        Mode.Signature | Mode.Application, 2)
    balance           = OpType("balance",           Mode.Application,                  2)
    app_opted_in      = OpType("app_opted_in",      Mode.Application,                  2)
    app_local_get     = OpType("app_local_get",     Mode.Application,                  2)
    app_local_get_ex  = OpType("app_local_get_ex",  Mode.Application,                  2)
    app_global_get    = OpType("app_global_get",    Mode.Application,                  2)
    app_global_get_ex = OpType("app_global_get_ex", Mode.Application,                  2)
    app_local_put     = OpType("app_local_put",     Mode.Application,                  2)
    app_global_put    = OpType("app_global_put",    Mode.Application,                  2)
    app_local_del     = OpType("app_local_del",     Mode.Application,                  2)
    app_global_del    = OpType("app_global_del",    Mode.Application,                  2)
    asset_holding_get = OpType("asset_holding_get", Mode.Application,                  2)
    asset_params_get  = OpType("asset_params_get",  Mode.Application,                  2)
    gtxns             = OpType("gtxns",             Mode.Signature | Mode.Application, 3)
    gtxnsa            = OpType("gtxnsa",            Mode.Signature | Mode.Application, 3)
    assert_           = OpType("assert",            Mode.Signature | Mode.Application, 3)
    dig               = OpType("dig",               Mode.Signature | Mode.Application, 3)
    swap              = OpType("swap",              Mode.Signature | Mode.Application, 3)
    select            = OpType("select",            Mode.Signature | Mode.Application, 3)
    getbit            = OpType("getbit",            Mode.Signature | Mode.Application, 3)
    setbit            = OpType("setbit",            Mode.Signature | Mode.Application, 3)
    getbyte           = OpType("getbyte",           Mode.Signature | Mode.Application, 3)
    setbyte           = OpType("setbyte",           Mode.Signature | Mode.Application, 3)
    min_balance       = OpType("min_balance",       Mode.Application,                  3)
    pushbytes         = OpType("pushbytes",         Mode.Signature | Mode.Application, 3)
    pushint           = OpType("pushint",           Mode.Signature | Mode.Application, 3)

Op.__module__ = "pyteal"
