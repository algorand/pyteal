from ast import Sub
from cmath import exp
from pathlib import Path

from pyteal import *
from pyteal.types import require_type


# HELPERS:


def compile_and_save(approval):
    teal = Path.cwd() / "tests" / "teal"
    compiled = compileTeal(approval(), mode=Mode.Application, version=6)
    name = approval.__name__
    with open(teal / (name + ".teal"), "w") as f:
        f.write(compiled)
    return teal, name, compiled


def mismatch_ligature(expected, actual):
    la, le = len(actual), len(expected)
    mm_idx = -1
    for i in range(min(la, le)):
        if expected[i] != actual[i]:
            mm_idx = i
            break
    if mm_idx < 0:
        return ""
    return " " * (mm_idx) + "X" + "-" * (max(la, le) - mm_idx - 1)


def assert_teal_as_expected(path2actual, path2expected):

    with open(path2actual, "r") as fa, open(path2expected, "r") as fe:
        alines = fa.read().split("\n")
        elines = fe.read().split("\n")

        assert len(elines) == len(
            alines
        ), f"""EXPECTED {len(elines)} lines for {path2expected}
but ACTUALLY got {len(alines)} lines in {path2actual}"""

        for i, actual in enumerate(alines):
            expected = elines[i]
            assert expected.startswith(
                actual
            ), f"""ACTUAL line in {path2actual}
LINE{i+1}:
{actual}
{mismatch_ligature(expected, actual)}
DOES NOT prefix the EXPECTED (which should have been actual + some commentary) in {path2expected}:
LINE{i+1}:
{expected}  
{mismatch_ligature(expected, actual)}
"""


def assert_new_v_old(dynamic_scratch):
    teal_dir, name, compiled = compile_and_save(dynamic_scratch)
    print(
        f"""Compilation resulted in TEAL program of length {len(compiled)}. 
To view output SEE <{name}.teal> in ({teal_dir})
--------------"""
    )

    path2actual = teal_dir / (name + ".teal")
    path2expected = teal_dir / (name + "_expected.teal")
    assert_teal_as_expected(path2actual, path2expected)


# PYTEALS:


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


if __name__ == "__main__":
    for pt in (dynamic_scratch, dynamic_scratch_2, wilt_the_stilt):
        assert_new_v_old(pt)

    teal_dir, name, compiled = compile_and_save(wilt_the_stilt)
