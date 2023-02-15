""" Rock Paper Scissors example taken from https://github.com/gr8h/project_rps (15 Feb 2023)
"""

from base64 import b64decode
from dataclasses import dataclass
from typing import Dict

from algosdk.v2client.algod import AlgodClient
from pyteal import *
from pyteal.ast import *


def event(
    init: Expr = Reject(),
    delete: Expr = Reject(),
    update: Expr = Reject(),
    opt_in: Expr = Reject(),
    close_out: Expr = Reject(),
    no_op: Expr = Reject(),
) -> Expr:
    return Cond(
        [Txn.application_id() == Int(0), init],
        [Txn.on_completion() == OnComplete.DeleteApplication, delete],
        [Txn.on_completion() == OnComplete.UpdateApplication, update],
        [Txn.on_completion() == OnComplete.OptIn, opt_in],
        [Txn.on_completion() == OnComplete.CloseOut, close_out],
        [Txn.on_completion() == OnComplete.NoOp, no_op],
    )


def check_rekey_zero(
    num_transactions: int,
):
    return Assert(
        And(
            *[
                Gtxn[i].rekey_to() == Global.zero_address()
                for i in range(num_transactions)
            ]
        )
    )


def check_self(
    group_size: Expr = Int(1),
    group_index: Expr = Int(0),
):
    return Assert(
        And(
            Global.group_size() == group_size,
            Txn.group_index() == group_index,
        )
    )


def application(pyteal: Expr) -> str:
    return compileTeal(pyteal, mode=Mode.Application, version=MAX_TEAL_VERSION)


@dataclass
class CompiledSignature:
    address: str
    bytecode_b64: str
    teal: str


def signature(algod_client: AlgodClient, pyteal: Expr) -> CompiledSignature:
    teal = compileTeal(pyteal, mode=Mode.Signature, version=MAX_TEAL_VERSION)
    compilation_result = algod_client.compile(teal)
    return CompiledSignature(
        address=compilation_result["hash"],
        bytecode_b64=compilation_result["result"],
        teal=teal,
    )
