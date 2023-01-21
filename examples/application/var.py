from typing import Literal
from pyteal import (
    abi,
    Subroutine,
    OptimizeOptions,
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

# Just making sure it works for subrs
@Subroutine(TealType.uint64)
def add_vars(a: Expr, b: Expr) -> Expr:
    return a + b


# This method allows us to return a seq
# instead of the Var Expr itself
# so we dont have to do weird stuff to get
# around the type checking
def assign(*vars: Var) -> Expr:
    return Seq(*[v.assign() for v in vars])


# Note: v += z does _not_ work and produces a syntax error

program = Seq(
    # Types can be added directly
    assign(
        v := Var(1),
        z := Var(3),
        # Subroutines ok?
        result := Var(add_vars(v, z)),
    ),
    Assert(v + z == result),
    #
    # Bytes can be concat'd with +
    #
    assign(
        lol := Var("lol."),
        lmao := Var("lmao."),
    ),
    Assert(lol + lmao == Bytes("lol.lmao.")),
    #
    # `cast` the type to coerce it from `anytype`
    #
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
        sv := Var(App.localGet(Int(0), Bytes("intkey")), type_cast=TealType.bytes),
        iv := Var(App.localGet(Int(0), Bytes("bytekey")), type_cast=TealType.uint64),
    ),
    Assert(Len(sv) > Int(0)),
    Assert(iv > Int(0)),
    # simplify for loop init?
    For(assign(i := Var(0)), i < Int(10), i(i + Int(1))).Do(Assert(i)),
    # ABI types?
    (half_int := abi.Uint32()).set(Int(123)),
    assign(n := Var(half_int.encode(), "uint32")),
    (arr := abi.make(abi.StaticArray[abi.Uint32, Literal[2]])).set(
        [half_int, half_int]
    ),
    assign(a := Var(arr.encode(), str(arr))),
    # Assert(a[0]>Int(0)),
    Int(1),
)

print(
    compileTeal(
        program,
        mode=Mode.Application,
        version=8,
        optimize=OptimizeOptions(scratch_slots=True, frame_pointers=True),
    )
)
