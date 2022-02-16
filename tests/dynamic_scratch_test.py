from pyteal import *

from .compile_asserts import assert_new_v_old, compile_and_save


def dynamic_scratch():
    current_player = ScratchVar(TealType.uint64, 128)
    player_score = ScratchVar(TealType.uint64, current_player.load())
    i = ScratchVar(TealType.uint64, 0)
    return Seq(
        current_player.store(Int(129)),
        For(i.store(Int(1)), i.load() <= Int(10), i.store(i.load() + Int(1))).Do(
            Seq(
                current_player.store(Int(129) + (i.load() - Int(1)) % Int(5)),
                Log(Concat(Bytes("Current player: "), Itob(current_player.load()))),
                Log(Concat(Bytes("Player score index: "), Itob(player_score.index()))),
                player_score.store(player_score.load() + i.load()),
            )
        ),
        Int(1),
    )


def dynamic_scratch_2():
    current_player = ScratchVar(TealType.uint64)
    player_score = ScratchVar(TealType.uint64, current_player.load())
    i = ScratchVar(TealType.uint64)
    return Seq(
        current_player.store(Int(129)),
        For(i.store(Int(1)), i.load() <= Int(10), i.store(i.load() + Int(1))).Do(
            Seq(
                current_player.store(Int(129) + (i.load() - Int(1)) % Int(5)),
                Log(Concat(Bytes("Current player: "), Itob(current_player.load()))),
                Log(Concat(Bytes("Player score index: "), Itob(player_score.index()))),
                player_score.store(player_score.load() + i.load()),
            )
        ),
        Int(1),
    )


def wilt_the_stilt():
    player_index = ScratchVar(TealType.uint64)
    player_score = ScratchVar(TealType.uint64, player_index.load())
    return Seq(
        player_index.store(Int(129)),  # Wilt Chamberlain
        player_score.store(Int(100)),
        player_index.store(Int(130)),  # Kobe Bryant
        player_score.store(Int(81)),
        player_index.store(Int(131)),  # David Thompson
        player_score.store(Int(73)),
        Assert(player_score.load() == Int(73)),
        Assert(player_score.index() == Int(131)),
        player_index.store(player_index.load() - Int(2)),  # back to Wilt:
        Assert(player_score.load() == Int(100)),
        Assert(player_score.index() == Int(129)),
        Int(100),
    )


@Subroutine(TealType.bytes)
def logcat(some_bytes, an_int):
    catted = ScratchVar(TealType.bytes)
    return Seq(
        catted.store(Concat(some_bytes, Itob(an_int))),
        Log(catted.load()),
        catted.load(),
    )


@Subroutine(TealType.bytes)
def logcat_dynamic(some_bytes, an_int):
    catted = ScratchVar(TealType.bytes, Int(42))
    return Seq(
        catted.store(Concat(some_bytes, Itob(an_int))),
        Log(catted.load()),
        catted.load(),
    )


@Subroutine(TealType.uint64)
def slow_fibonacci(n):
    return (
        If(n <= Int(1))
        .Then(n)
        .Else(slow_fibonacci(n - Int(2)) + slow_fibonacci(n - Int(1)))
    )


@Subroutine(TealType.uint64)
def fast_fibonacci(n):
    i = ScratchVar(TealType.uint64)
    a = ScratchVar(TealType.uint64)
    b = ScratchVar(TealType.uint64)
    return Seq(
        a.store(Int(0)),
        b.store(Int(1)),
        For(i.store(Int(1)), i.load() <= n, i.store(i.load() + Int(1))).Do(
            Seq(
                b.store(a.load() + b.load()),
                a.store(b.load() - a.load()),
            )
        ),
        a.load(),
    )


@Subroutine(TealType.uint64)
def fast_fibonacci_mixed(n):
    i = ScratchVar(TealType.uint64, Int(42))
    a = ScratchVar(
        TealType.uint64, Int(42) * Int(1337)
    )  # yes, this is too big - but the compiler can't figure that out
    b = ScratchVar(TealType.uint64)
    return Seq(
        a.store(Int(0)),
        b.store(Int(1)),
        For(i.store(Int(1)), i.load() <= n, i.store(i.load() + Int(1))).Do(
            Seq(
                b.store(a.load() + b.load()),
                a.store(b.load() - a.load()),
            )
        ),
        a.load(),
    )


def subroutines():
    selected = ScratchVar(TealType.bytes, Int(1337))
    hello = ScratchVar(
        TealType.bytes,
    )
    hello_dyn = ScratchVar(TealType.bytes, Int(747))
    x_reg = ScratchVar(TealType.uint64)
    x_dyn = ScratchVar(TealType.uint64, Int(777))
    return Seq(
        hello.store(Bytes("hello there")),
        hello_dyn.store(Bytes("goodbye")),
        x_reg.store(Int(1_000_000)),
        x_dyn.store(Int(1_000_000_000)),
        selected.store(Bytes("fast_fibonacci_mixed")),
        If(selected.load() == Bytes("logcat"))
        .Then(
            Seq(
                Pop(logcat(hello.load(), Int(17))),
                Int(100),
            )
        )
        .ElseIf(
            Concat(Bytes("logcat"), Bytes("_"), Bytes("dynamic")) == selected.load()
        )
        .Then(
            Seq(
                Pop(logcat_dynamic(Bytes("yo"), Int(117))),
                Pop(logcat_dynamic(hello.load(), x_reg.load())),
                Pop(logcat_dynamic(hello_dyn.load(), x_dyn.load())),
                Int(101),
            )
        )
        .ElseIf(selected.load() == Bytes("slow_fibonacci"))
        .Then(
            Seq(
                Pop(slow_fibonacci(Int(217))),
                Pop(slow_fibonacci(x_reg.load())),
                slow_fibonacci(x_dyn.load()),
            )
        )
        .ElseIf(selected.load() == Bytes("fast_fibonacci"))
        .Then(
            Seq(
                Pop(fast_fibonacci(Int(317))),
                Pop(fast_fibonacci(x_reg.load())),
                fast_fibonacci(x_dyn.load()),
            )
        )
        .ElseIf(selected.load() == Bytes("fast_fibonacci_mixed"))
        .Then(
            Seq(
                Pop(fast_fibonacci_mixed(Int(417))),
                Pop(fast_fibonacci_mixed(x_reg.load())),
                fast_fibonacci_mixed(x_dyn.load()),
            )
        )
        .Else(
            Err(),
        ),
    )


# TEST_CASES = (dynamic_scratch, dynamic_scratch_2, wilt_the_stilt, subroutines)

TEST_CASES = (wilt_the_stilt,)


def test_all():
    for pt in TEST_CASES:
        assert_new_v_old(pt)


def test_generate_another():
    teal_dir, name, compiled = compile_and_save(subroutines)
    print(
        f"""Successfuly tested approval program <<{name}>> having 
compiled it into {len(compiled)} characters. See the results in:
{teal_dir}
"""
    )


if __name__ == "__main__":
    test_all()
