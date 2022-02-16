from pyteal import *

from compile_asserts import assert_new_v_old, compile_and_save


@Subroutine(TealType.none)
def swap(x: ScratchVar, y: ScratchVar):
    z = ScratchVar(TealType.anytype)
    return Seq(
        z.store(x.load()),
        x.store(y.load()),
        y.store(z.load()),
    )


def swapper():
    a = ScratchVar(TealType.bytes)
    b = ScratchVar(TealType.bytes)
    return Seq(
        a.store(Bytes("hello")),
        b.store(Bytes("goodbye")),
        swap(a, b),
        Assert(a.load() == Bytes("goodbye")),
        Assert(b.load() == Bytes("hello")),
        Int(1000),
    )


@Subroutine(TealType.none)
def factorial(n: ScratchVar):
    tmp = ScratchVar(TealType.uint64)
    return (
        If(n.load() <= 1)
        .Then(n.store(Int(1)))
        .Else(
            Seq(
                tmp.store(n.load() - Int(1)),
                factorial(tmp),
                n.store(n * tmp.load()),
            )
        )
    )


def fac_by_ref():
    n = ScratchVar(TealType.uint64)
    return Seq(
        n.store(Int(42)),
        factorial(n),
        n.load(),
    )


TEST_CASES = (swapper,)


def test_all():
    for pt in TEST_CASES:
        assert_new_v_old(pt)


def test_generate_another():
    teal_dir, name, compiled = compile_and_save(swapper)
    print(
        f"""Successfuly tested approval program <<{name}>> having 
compiled it into {len(compiled)} characters. See the results in:
{teal_dir}
"""
    )


if __name__ == "__main__":
    test_generate_another()
