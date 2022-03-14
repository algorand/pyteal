from typing import Callable
import pytest

from algosdk import kmd
from algosdk.v2client import algod, indexer

from pyteal import *

# from .pass_by_ref_test import oldfac

# TODO: refactor these into utility

## Clients


def _kmd_client(kmd_address="http://localhost:4002", kmd_token="a" * 64):
    """Instantiate and return a KMD client object."""
    return kmd.KMDClient(kmd_token, kmd_address)


def _algod_client(algod_address="http://localhost:4001", algod_token="a" * 64):
    """Instantiate and return Algod client object."""
    return algod.AlgodClient(algod_token, algod_address)


def _indexer_client(indexer_address="http://localhost:8980", indexer_token="a" * 64):
    """Instantiate and return Indexer client object."""
    return indexer.IndexerClient(indexer_token, indexer_address)


def get_clients():
    try:
        kmd = _kmd_client()
    except Exception as e:
        raise Exception("kmd is missing from environment") from e

    try:
        algod = _algod_client()
    except Exception as e:
        raise Exception("algod is missing from environment") from e

    return kmd, algod


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


SEMANTIC_CASES = [exp, square, swap, string_mult, oldfac]
if not SEMANTIC_TESTING:
    SEMANTIC_CASES = []


def semantic_e2e_factory(subr: SubroutineFnWrapper, mode: Mode) -> Callable[..., Expr]:
    input_types = subr.subroutine.input_types
    arg_names = subr.subroutine.arguments()

    def arg_prep_n_call(i, p):
        name = arg_names[i]
        by_ref = name in subr.subroutine.by_ref_args
        x = subr
        arg_expr = Txn.application_args[i] if mode == Mode.Application else Arg(i)
        if p == TealType.uint64:
            arg_expr = Btoi(arg_expr)
        prep = None
        arg_var = arg_expr
        if by_ref:
            arg_var = ScratchVar(p)
            prep = arg_var.store(arg_expr)
        return prep, arg_var

    def subr_caller():
        preps_n_calls = [*(arg_prep_n_call(i, p) for i, p in enumerate(input_types))]
        preps, calls = zip(*preps_n_calls) if preps_n_calls else ([], [])
        preps = [p for p in preps if p]
        invocation = subr(*calls)
        if preps:
            return Seq(*(preps + [invocation]))
        return invocation

    def make_return(e):
        if e.type_of() == TealType.uint64:
            return e
        if e.type_of() == TealType.bytes:
            return Btoi(e)
        return Seq(e, Int(1339))

    def make_log(e):
        if e.type_of() == TealType.uint64:
            return Log(Itob(e))
        if e.type_of() == TealType.bytes:
            return Log(e)
        return Log(Bytes("nada"))

    if mode == Mode.Signature:

        def approval():
            return make_return(subr_caller())

    else:

        def approval():
            result = ScratchVar(subr.subroutine.returnType)
            return Seq(
                result.store(subr_caller()),
                make_log(result.load()),
                make_return(result.load()),
            )

    setattr(approval, "__name__", f"sem_{mode}_{subr.name()}")
    return approval


@pytest.mark.parametrize("mode", [Mode.Signature, Mode.Application])
@pytest.mark.parametrize("subr", SEMANTIC_CASES)
def test_semantic(subr: SubroutineFnWrapper, mode: Mode):
    assert isinstance(subr, SubroutineFnWrapper), f"unexpected subr type {type(subr)}"
    print(f"semantic e2e test of {subr.name()}")
    approval = semantic_e2e_factory(subr, mode)
    teal = compileTeal(approval(), mode, version=6, assembleConstants=True)
    print(
        f"""subroutine {subr.name()}@{mode}:
-------
{teal}
-------"""
    )

    kmd, algod = get_clients()


# if __name__ == "__main__":
#     test_semantic(oldfac)
#     test_semantic(swap)
#     test_semantic(string_mult)
