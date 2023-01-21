from pyteal import (
    For,
    Len,
    App,
    Mode,
    Int,
    Seq,
    compileTeal,
    TealType,
    Assert,
    Bytes,
    Expr,
    Var,
)


def assign(*vars: Var) -> Expr:
    return Seq(*[v.assign() for v in vars])


program = Seq(
    # Types can be added directly
    assign(
        v := Var(1),
        z := Var(3),
    ),
    Assert(v + z == Int(4)),
    # Note: v += z does _not_ work because python thinks its a statement?
    #
    # Bytes can be concat'd with +
    assign(
        lol := Var("lol."),
        lmao := Var("lmao."),
    ),
    Assert(lol + lmao == Bytes("lol.lmao.")),
    #
    # `cast` the type to coerce it
    assign(
        iv := Var(App.localGet(Int(0), Bytes("intkey")), type_cast=TealType.uint64),
        sv := Var(App.localGet(Int(0), Bytes("bytekey")), type_cast=TealType.bytes),
    ),
    Assert(iv > Int(0)),
    Assert(Len(sv) > Int(0)),
    #
    # auto convert with itob/btoi, too fancy?
    #
    assign(
        iv := Var(App.localGet(Int(0), Bytes("intkey")), type_cast=TealType.bytes),
        sv := Var(App.localGet(Int(0), Bytes("bytekey")), type_cast=TealType.uint64),
    ),
    Assert(Len(sv) > Int(0)),
    Assert(iv > Int(0)),
    ###
    Int(1),
)
print(compileTeal(program, mode=Mode.Application, version=6))
