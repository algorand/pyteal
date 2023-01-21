from pyteal import (
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


def range(v: Var, stop: int | Expr) -> list[Expr]:
    # only allows incr by 1
    if type(stop) is int:
        stop = Int(stop)
    return [assign(v), v < stop, v.incr()]


program = Seq(
    # Types can be added directly
    assign(
        v := Var(1),
        z := Var(3),
    ),
    Assert(v + z == Int(4)),
    # Subroutines ok?
    assign(result := Var(add_vars(v, z))),
    Assert(result == Int(4)),
    # Note: v += z does _not_ work and produces a syntax error
    #
    # Bytes can be concat'd with +
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
        iv := Var(App.localGet(Int(0), Bytes("intkey")), type_cast=TealType.bytes),
        sv := Var(App.localGet(Int(0), Bytes("bytekey")), type_cast=TealType.uint64),
    ),
    Assert(Len(sv) > Int(0)),
    Assert(iv > Int(0)),
    # simplify the for loop, not strictly related to Var
    # but nicer either way
    For(*range(i := Var(0), 10)).Do(Assert(i)),
    # ##
    # TODO: add bigint to supported types for big int byte math?
    # ##
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
