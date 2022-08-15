from pyteal import Seq, Subroutine, TealType, Assert, Int, compileTeal, Mode


@Subroutine(TealType.uint64)
def tst_subr():
    return Seq(Assert((Int(0), "newp")), Int(1))


program = Seq(
    # Make this be
    Assert((Int(1), "ok")),
    # On different
    Assert((Int(1), "no way"), (Int(1), "wow")),
    # lines
    tst_subr(),
)


print(compileTeal(program, mode=Mode.Application, version=7, debug=False))
