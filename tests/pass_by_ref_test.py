from pyteal import *

from .compile_asserts import assert_new_v_old, compile_and_save


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


TEST_CASES = (swapper,)


def test_all():
    for pt in TEST_CASES:
        assert_new_v_old(pt)


def test_generate_another():
    teal_dir, name, compiled = compile_and_save(swapper)
    print(
        f"""Successfuly tested approval program {name} having 
compiled it into {len(compiled)} characters. See the results in:
{teal_dir}
"""
    )


if __name__ == "__main__":
    test_generate_another()
