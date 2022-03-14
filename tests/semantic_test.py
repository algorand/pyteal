import pytest

from algosdk.testing.dryrun import Helper as DryRunHelper

from .semantic_asserts import (
    _algod_client,
    e2e_teal,
    lightly_encode_args,
    lightly_encode_output,
)

from pyteal import *


@Subroutine(TealType.uint64, input_types=[])
def exp():
    return Int(2) ** Int(10)


@Subroutine(TealType.none, input_types=[TealType.uint64])
def square(x: ScratchVar):
    return x.store(x.load() * x.load())


@Subroutine(TealType.none, input_types=[TealType.anytype, TealType.anytype])
def swap(x: ScratchVar, y: ScratchVar):
    z = ScratchVar(TealType.anytype)
    return Seq(
        z.store(x.load()),
        x.store(y.load()),
        y.store(z.load()),
    )


@Subroutine(TealType.bytes, input_types=[TealType.bytes, TealType.uint64])
def string_mult(s: ScratchVar, n):
    i = ScratchVar(TealType.uint64)
    tmp = ScratchVar(TealType.bytes)
    start = Seq(i.store(Int(1)), tmp.store(s.load()), s.store(Bytes("")))
    step = i.store(i.load() + Int(1))
    return Seq(
        For(start, i.load() <= n, step).Do(s.store(Concat(s.load(), tmp.load()))),
        s.load(),
    )


@Subroutine(TealType.uint64, input_types=[TealType.uint64])
def oldfac(n):
    return If(n < Int(2)).Then(Int(1)).Else(n * oldfac(n - Int(1)))


SEMANTIC_TESTING = True

SCENARIOS = {
    exp: {"args": [[]]},
    square: {"args": [[i] for i in range(100)]},
    swap: {"args": [[1, 2], [1, "two"], ["one", 2], ["one", "two"]]},
    string_mult: {"args": [["xyzw", i] for i in range(100)]},
    oldfac: {"args": [[i] for i in range(25)]},
}

SEMANTIC_CASES = SCENARIOS.keys()
if not SEMANTIC_TESTING:
    SEMANTIC_CASES = []


@pytest.mark.parametrize("mode", [Mode.Signature, Mode.Application])
@pytest.mark.parametrize("subr", SEMANTIC_CASES)
def test_semantic(subr: SubroutineFnWrapper, mode: Mode):
    case_name = subr.name()
    assert isinstance(subr, SubroutineFnWrapper), f"unexpected subr type {type(subr)}"
    print(f"semantic e2e test of {case_name}")
    approval = e2e_teal(subr, mode)
    teal = compileTeal(approval(), mode, version=6, assembleConstants=True)
    print(
        f"""subroutine {case_name}@{mode}:
-------
{teal}
-------"""
    )
    algod = _algod_client()

    dr_builder = (
        DryRunHelper.build_simple_app_request
        if mode == Mode.Application
        else DryRunHelper.build_simple_lsig_request
    )
    dry_run_reqs = list(
        map(
            lambda args: dr_builder(teal, lightly_encode_args(args)),
            SCENARIOS[subr]["args"],
        )
    )
    dry_run_resps = list(map(algod.dryrun, dry_run_reqs))
    x = 42
    # dry_run_req =

    # kmd, algod = get_clients()


# if __name__ == "__main__":
#     test_semantic(oldfac)
#     test_semantic(swap)
#     test_semantic(string_mult)
