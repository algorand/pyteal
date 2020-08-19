from enum import Enum, Flag, auto

class Mode(Flag):
    """Enum of program running modes."""
    
    Signature = auto()
    Application = auto()

Mode.__module__ = "pyteal"

class Op(Enum):
    """Enum of program opcodes."""

    err = "err", Mode.Signature | Mode.Application
    sha256 = "sha256", Mode.Signature | Mode.Application
    keccak256 = "keccak256", Mode.Signature | Mode.Application
    sha512_256 = "sha512_256", Mode.Signature | Mode.Application
    ed25519verify = "ed25519verify", Mode.Signature
    add = "+", Mode.Signature | Mode.Application
    minus = "-", Mode.Signature | Mode.Application
    div = "/", Mode.Signature | Mode.Application
    mul = "*", Mode.Signature | Mode.Application
    lt = "<", Mode.Signature | Mode.Application
    gt = ">", Mode.Signature | Mode.Application
    le = "<=", Mode.Signature | Mode.Application
    ge = ">=", Mode.Signature | Mode.Application
    logic_and = "&&", Mode.Signature | Mode.Application
    logic_or = "||", Mode.Signature | Mode.Application
    eq = "==", Mode.Signature | Mode.Application
    neq = "!=", Mode.Signature | Mode.Application
    logic_not = "!", Mode.Signature | Mode.Application
    len = "len", Mode.Signature | Mode.Application
    itob = "itob", Mode.Signature | Mode.Application
    btoi = "btoi", Mode.Signature | Mode.Application
    mod = "%", Mode.Signature | Mode.Application
    bitwise_or = "|", Mode.Signature | Mode.Application
    bitwise_and = "&", Mode.Signature | Mode.Application
    bitwise_xor = "^", Mode.Signature | Mode.Application
    bitwise_not = "~", Mode.Signature | Mode.Application
    mulw = "mulw", Mode.Signature | Mode.Application
    addw = "addw", Mode.Signature | Mode.Application
    int = "int", Mode.Signature | Mode.Application
    byte = "byte", Mode.Signature | Mode.Application
    addr = "addr", Mode.Signature | Mode.Application
    arg = "arg", Mode.Signature
    txn = "txn", Mode.Signature | Mode.Application
    global_ = "global", Mode.Signature | Mode.Application
    gtxn = "gtxn", Mode.Signature | Mode.Application
    load = "load", Mode.Signature | Mode.Application
    store = "store", Mode.Signature | Mode.Application
    txna = "txna", Mode.Signature | Mode.Application
    gtxna = "gtxna", Mode.Signature | Mode.Application
    bnz = "bnz", Mode.Signature | Mode.Application
    bz = "bz", Mode.Signature | Mode.Application
    b = "b", Mode.Signature | Mode.Application
    return_ = "return", Mode.Signature | Mode.Application
    pop = "pop", Mode.Signature | Mode.Application
    dup = "dup", Mode.Signature | Mode.Application
    dup2 = "dup2", Mode.Signature | Mode.Application
    concat = "concat", Mode.Signature | Mode.Application
    substring = "substring", Mode.Signature | Mode.Application
    substring3 = "substring3", Mode.Signature | Mode.Application
    balance = "balance", Mode.Application
    app_opted_in = "app_opted_in", Mode.Application
    app_local_get = "app_local_get", Mode.Application
    app_local_get_ex = "app_local_get_ex", Mode.Application
    app_global_get = "app_global_get", Mode.Application
    app_global_get_ex = "app_global_get_ex", Mode.Application
    app_local_put = "app_local_put", Mode.Application
    app_global_put = "app_global_put", Mode.Application
    app_local_del = "app_local_del", Mode.Application
    app_global_del = "app_global_del", Mode.Application
    asset_holding_get = "asset_holding_get", Mode.Application
    asset_params_get = "asset_params_get", Mode.Application

    def __new__(cls, value: str, mode: Mode):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value: str, mode: Mode):
        self.mode = mode

Op.__module__ = "pyteal"
