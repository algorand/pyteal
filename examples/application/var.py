from pyteal import (
    Len,
    App,
    Mode,
    Int,
    Seq,
    compileTeal,
    TealType,
    Assert,
    Bytes,
    Var,
)

program = Seq(
    # Types can be added directly
    v := Var(Int(1)),
    z := Var(Int(3)),
    Assert(v + z == Int(4)),
    # v += z does _not_ work because python thinks its a statement?
    #
    # Bytes can be concat'd with +
    lol := Var(Bytes("lol.")),
    lmao := Var(Bytes("lmao.")),
    Assert(lol + lmao == Bytes("lol.lmao.")),
    #
    # `cast` the type to coerce it
    # note: you have to `load` it if its type is checked without special
    # handling
    iv := Var(App.localGet(Int(0), Bytes("intkey")), type_cast=TealType.uint64),
    Assert(iv.load() > Int(0)),
    sv := Var(App.localGet(Int(0), Bytes("bytekey")), type_cast=TealType.bytes),
    Assert(Len(sv.load()) > Int(0)),
    #
    # auto convert with itob/btoi, too fancy?
    #
    iv := Var(App.localGet(Int(0), Bytes("intkey")), type_cast=TealType.bytes),
    Assert(Len(sv.load()) > Int(0)),
    sv := Var(App.localGet(Int(0), Bytes("bytekey")), type_cast=TealType.uint64),
    Assert(iv.load() > Int(0)),
    Int(1),
)
print(compileTeal(program, mode=Mode.Application, version=6))
