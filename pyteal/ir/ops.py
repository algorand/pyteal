from typing import NamedTuple
from enum import Enum, Flag, auto

class Mode(Flag):
    """Enum of program running modes."""
    
    Signature = auto()
    Application = auto()

Mode.__module__ = "pyteal"

OpEffects = NamedTuple('OpEffects', [('pops', int), ('pushes', int)])
OpType = NamedTuple('OpType', [('value', str), ('mode', Mode), ('min_version', int), ('effects', OpEffects)])

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
    
    @property
    def pops(self) -> int:
        """Get the number of values this op pops from the stack when ran."""
        return self.value.effects.pops
    
    @property
    def pushes(self) -> int:
        """Get the number of values this op pushes to the stack when ran."""
        return self.value.effects.pushes

    err               = OpType("err",               Mode.Signature | Mode.Application, 2, OpEffects(0, 0))
    sha256            = OpType("sha256",            Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    keccak256         = OpType("keccak256",         Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    sha512_256        = OpType("sha512_256",        Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    ed25519verify     = OpType("ed25519verify",     Mode.Signature,                    2, OpEffects(3, 1))
    add               = OpType("+",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    minus             = OpType("-",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    div               = OpType("/",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    mul               = OpType("*",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    lt                = OpType("<",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    gt                = OpType(">",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    le                = OpType("<=",                Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    ge                = OpType(">=",                Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    logic_and         = OpType("&&",                Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    logic_or          = OpType("||",                Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    eq                = OpType("==",                Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    neq               = OpType("!=",                Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    logic_not         = OpType("!",                 Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    len               = OpType("len",               Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    itob              = OpType("itob",              Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    btoi              = OpType("btoi",              Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    mod               = OpType("%",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    bitwise_or        = OpType("|",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    bitwise_and       = OpType("&",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    bitwise_xor       = OpType("^",                 Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    bitwise_not       = OpType("~",                 Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    mulw              = OpType("mulw",              Mode.Signature | Mode.Application, 2, OpEffects(2, 2))
    addw              = OpType("addw",              Mode.Signature | Mode.Application, 2, OpEffects(2, 2))
    intcblock         = OpType("intcblock",         Mode.Signature | Mode.Application, 2, OpEffects(0, 0))
    intc              = OpType("intc",              Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    intc_0            = OpType("intc_0",            Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    intc_1            = OpType("intc_1",            Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    intc_2            = OpType("intc_2",            Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    intc_3            = OpType("intc_3",            Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    int               = OpType("int",               Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    bytecblock        = OpType("bytecblock",        Mode.Signature | Mode.Application, 2, OpEffects(0, 0))
    bytec             = OpType("bytec",             Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    bytec_0           = OpType("bytec_0",           Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    bytec_1           = OpType("bytec_1",           Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    bytec_2           = OpType("bytec_2",           Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    bytec_3           = OpType("bytec_3",           Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    byte              = OpType("byte",              Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    addr              = OpType("addr",              Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    arg               = OpType("arg",               Mode.Signature,                    2, OpEffects(0, 1))
    txn               = OpType("txn",               Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    global_           = OpType("global",            Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    gtxn              = OpType("gtxn",              Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    load              = OpType("load",              Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    store             = OpType("store",             Mode.Signature | Mode.Application, 2, OpEffects(1, 0))
    txna              = OpType("txna",              Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    gtxna             = OpType("gtxna",             Mode.Signature | Mode.Application, 2, OpEffects(0, 1))
    bnz               = OpType("bnz",               Mode.Signature | Mode.Application, 2, OpEffects(1, 0))
    bz                = OpType("bz",                Mode.Signature | Mode.Application, 2, OpEffects(1, 0))
    b                 = OpType("b",                 Mode.Signature | Mode.Application, 2, OpEffects(0, 0))
    return_           = OpType("return",            Mode.Signature | Mode.Application, 2, OpEffects(1, 0))
    pop               = OpType("pop",               Mode.Signature | Mode.Application, 2, OpEffects(1, 0))
    dup               = OpType("dup",               Mode.Signature | Mode.Application, 2, OpEffects(1, 2))
    dup2              = OpType("dup2",              Mode.Signature | Mode.Application, 2, OpEffects(2, 4))
    concat            = OpType("concat",            Mode.Signature | Mode.Application, 2, OpEffects(2, 1))
    substring         = OpType("substring",         Mode.Signature | Mode.Application, 2, OpEffects(1, 1))
    substring3        = OpType("substring3",        Mode.Signature | Mode.Application, 2, OpEffects(3, 1))
    balance           = OpType("balance",           Mode.Application,                  2, OpEffects(1, 1))
    app_opted_in      = OpType("app_opted_in",      Mode.Application,                  2, OpEffects(2, 1))
    app_local_get     = OpType("app_local_get",     Mode.Application,                  2, OpEffects(2, 1))
    app_local_get_ex  = OpType("app_local_get_ex",  Mode.Application,                  2, OpEffects(3, 2))
    app_global_get    = OpType("app_global_get",    Mode.Application,                  2, OpEffects(1, 1))
    app_global_get_ex = OpType("app_global_get_ex", Mode.Application,                  2, OpEffects(2, 2))
    app_local_put     = OpType("app_local_put",     Mode.Application,                  2, OpEffects(3, 0))
    app_global_put    = OpType("app_global_put",    Mode.Application,                  2, OpEffects(2, 0))
    app_local_del     = OpType("app_local_del",     Mode.Application,                  2, OpEffects(2, 0))
    app_global_del    = OpType("app_global_del",    Mode.Application,                  2, OpEffects(1, 0))
    asset_holding_get = OpType("asset_holding_get", Mode.Application,                  2, OpEffects(2, 2))
    asset_params_get  = OpType("asset_params_get",  Mode.Application,                  2, OpEffects(1, 2))
    gtxns             = OpType("gtxns",             Mode.Signature | Mode.Application, 3, OpEffects(1, 1))
    gtxnsa            = OpType("gtxnsa",            Mode.Signature | Mode.Application, 3, OpEffects(1, 1))
    assert_           = OpType("assert",            Mode.Signature | Mode.Application, 3, OpEffects(1, 0))
    dig               = OpType("dig",               Mode.Signature | Mode.Application, 3, OpEffects(0, 1)) # NOTE: dig can read values in the stack without popping them
    swap              = OpType("swap",              Mode.Signature | Mode.Application, 3, OpEffects(2, 2))
    select            = OpType("select",            Mode.Signature | Mode.Application, 3, OpEffects(3, 1))
    getbit            = OpType("getbit",            Mode.Signature | Mode.Application, 3, OpEffects(1, 1))
    setbit            = OpType("setbit",            Mode.Signature | Mode.Application, 3, OpEffects(3, 1))
    getbyte           = OpType("getbyte",           Mode.Signature | Mode.Application, 3, OpEffects(2, 1))
    setbyte           = OpType("setbyte",           Mode.Signature | Mode.Application, 3, OpEffects(3, 1))
    min_balance       = OpType("min_balance",       Mode.Application,                  3, OpEffects(1, 1))
    pushbytes         = OpType("pushbytes",         Mode.Signature | Mode.Application, 3, OpEffects(0, 1))
    pushint           = OpType("pushint",           Mode.Signature | Mode.Application, 3, OpEffects(0, 1))
    shl               = OpType("shl",               Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    shr               = OpType("shr",               Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    sqrt              = OpType("sqrt",              Mode.Signature | Mode.Application, 4, OpEffects(1, 1))
    bitlen            = OpType("bitlen",            Mode.Signature | Mode.Application, 4, OpEffects(1, 1))
    exp               = OpType("exp",               Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    divmodw           = OpType("divmodw",           Mode.Signature | Mode.Application, 4, OpEffects(4, 4))
    expw              = OpType("expw",              Mode.Signature | Mode.Application, 4, OpEffects(2, 2))
    b_add             = OpType("b+",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_minus           = OpType("b-",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_div             = OpType("b/",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_mul             = OpType("b*",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_lt              = OpType("b<",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_gt              = OpType("b>",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_le              = OpType("b<=",               Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_ge              = OpType("b>=",               Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_eq              = OpType("b==",               Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_neq             = OpType("b!=",               Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_mod             = OpType("b%",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_or              = OpType("b|",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_and             = OpType("b&",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_xor             = OpType("b^",                Mode.Signature | Mode.Application, 4, OpEffects(2, 1))
    b_not             = OpType("b~",                Mode.Signature | Mode.Application, 4, OpEffects(1, 1))
    bzero             = OpType("bzero",             Mode.Signature | Mode.Application, 4, OpEffects(1, 1))
    gload             = OpType("gload",             Mode.Application,                  4, OpEffects(0, 1))
    gloads            = OpType("gloads",            Mode.Application,                  4, OpEffects(1, 1))
    gaid              = OpType("gaid",              Mode.Application,                  4, OpEffects(0, 1))
    gaids             = OpType("gaids",             Mode.Application,                  4, OpEffects(1, 1))
    callsub           = OpType("callsub",           Mode.Signature | Mode.Application, 4, OpEffects(0, 0))
    retsub            = OpType("retsub",            Mode.Signature | Mode.Application, 4, OpEffects(0, 0))

Op.__module__ = "pyteal"
