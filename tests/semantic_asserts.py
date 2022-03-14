from typing import Callable, List, Union

from algosdk import kmd
from algosdk.v2client import algod, indexer

from pyteal import *

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


def e2e_teal(subr: SubroutineFnWrapper, mode: Mode) -> Callable[..., Expr]:
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
            return Len(e)
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


def lightly_encode_output(out: Union[int, str]) -> Union[int, str]:
    if isinstance(out, int):
        return out

    if isinstance(out, str):
        return bytes(out, "utf-8").hex()

    raise f"can't handle output [{out}] of type {type(out)}"


def lightly_encode_args(args: List[Union[str, int]]) -> List[str]:
    """
    Assumes int's are uint64 and
    """

    def encode(arg):
        assert isinstance(
            arg, (int, str)
        ), f"can't handle arg [{arg}] of type {type(arg)}"
        if isinstance(arg, int):
            assert arg >= 0, f"can't handle negative arguments but was given {arg}"
        return arg if isinstance(arg, str) else arg.to_bytes(8, byteorder="big")

    return [encode(a) for a in args]


# def dryrun_singleton(mode: Mode, teal: str, args):
#     pass
