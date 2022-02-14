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
        player_score.store(player_score.load() - Int(2)),  # back to Wilt:
        Assert(player_score.load() == Int(100)),
        Assert(player_score.index() == Int(129)),
        Int(100),
    )


TEST_CASES = (dynamic_scratch, dynamic_scratch_2, wilt_the_stilt)


def test_all():
    for pt in TEST_CASES:
        assert_new_v_old(pt)


def test_new():
    teal_dir, name, compiled = compile_and_save(wilt_the_stilt)
    print(
        f"""Successfuly tested approval program {name} having 
compiled it into {len(compiled)} characters. See the results in:
{teal_dir}
"""
    )
