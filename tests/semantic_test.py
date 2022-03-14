from base64 import b64decode
from enum import Enum
from typing import Any, Callable, Dict, List, Tuple, Union

import pytest

from algosdk.testing.dryrun import Helper as DryRunHelper

from .semantic_asserts import (
    e2e_teal,
    algod_with_assertion,
    lightly_encode_args,
    lightly_encode_output,
)

from pyteal import *

# TODO: these assertions belong in PySDK
from inspect import signature


class SequenceAssertion:
    def __init__(
        self,
        predicate: Union[Dict[Tuple, Union[str, int]], Callable],
        enforce: bool = True,
    ):
        self.definition = predicate
        self.predicate, self._expected = self.prepare_predicate(predicate)
        self.enforce = enforce

    def __repr__(self):
        return f"SequenceAssertion({self.definition})"[:100]

    def __call__(self, args: list, actual: Union[str, int]) -> bool:
        assertion = self.predicate(args, actual)
        if self.enforce:
            assert (
                assertion
            ), f"actual is [{actual}] BUT expected [{self.expected(args)}] for args {args}"
        return assertion

    def expected(self, args: list) -> Union[str, int]:
        return self._expected(args)

    def expected_type(self, args: list) -> type:
        return type(self.expected(args))

    @classmethod
    def prepare_predicate(cls, predicate):
        assert predicate, f"cannot prepare empty predicate {predicate}"
        if isinstance(predicate, dict):
            return (
                lambda args, actual: predicate[args] == actual,
                lambda args: predicate[args],
            )

        if not isinstance(predicate, Callable):
            # constant function in this case:
            return lambda _, actual: predicate == actual, lambda _: predicate

        try:
            sig = signature(predicate)
        except Exception as e:
            raise Exception(
                f"callable predicate {predicate} must have a signature"
            ) from e

        N = len(sig.parameters)
        assert N in (1, 2), f"predicate has the wrong number of paramters {N}"

        if N == 2:
            return predicate, lambda _: predicate

        return lambda args, actual: predicate(args) == actual, lambda args: predicate(
            args
        )


DryRunAssertionType = Enum("DryRunAssertionType", "lastLog stackTop status")
DRA = DryRunAssertionType


def mode_has_assertion(mode: Mode, assertion_type: DryRunAssertionType) -> bool:
    missing = {Mode.Signature: {DryRunAssertionType.lastLog}, Mode.Application: set()}
    if assertion_type in missing[mode]:
        return False

    return True


def dig_actual(
    mode: Mode, txn: dict, assert_type: DryRunAssertionType
) -> Union[str, int]:
    assert mode_has_assertion(
        mode, assert_type
    ), f"{mode} cannot handle dig information from txn for assertion type {assert_type}"

    if assert_type == DryRunAssertionType.lastLog:
        last_log = txn.get("logs", [None])[-1]
        if last_log is None:
            return last_log
        return b64decode(last_log).hex()

    if assert_type == DryRunAssertionType.status:
        return (
            txn["logic-sig-messages"][-1]
            if mode == Mode.Signature
            else txn["app-call-messages"][-1]
        )

    raise Exception(f"Unknown assert_type {assert_type}")


def dryrun_assert(
    inputs: List[list],
    dryrun_resps: List[dict],
    assert_type: DryRunAssertionType,
    assertion: SequenceAssertion,
):
    N = len(inputs)
    assert N == len(
        dryrun_resps
    ), f"inputs (len={N}) and dryrun responses (len={len(dryrun_resps)}) must have the same length"

    assert isinstance(
        assert_type, DryRunAssertionType
    ), f"assertions types must be DryRunAssertionType's but got [{assert_type}] which is a {type(assert_type)}"

    for i, args in enumerate(inputs):
        resp = dryrun_resps[i]
        txns = resp["txns"]
        assert len(txns) == 1, f"expecting exactly 1 transaction but got {len(txns)}"
        txn = txns[0]
        mode = Mode.Signature if "logic-sig-messages" in txn else Mode.Application

        actual = dig_actual(mode, txn, assert_type)
        assertion(args, actual)


@Subroutine(TealType.uint64, input_types=[])
def exp():
    return Int(2) ** Int(10)


@Subroutine(TealType.none, input_types=[TealType.uint64])
def square_byref(x: ScratchVar):
    return x.store(x.load() * x.load())


@Subroutine(TealType.uint64, input_types=[TealType.uint64])
def square(x):
    return x ** Int(2)


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
    exp: {
        "inputs": [[]],
        "assertions": {
            DRA.lastLog: lightly_encode_output(2 ** 10, logs=True),
            DRA.status: "PASS",
        },
    },
    square_byref: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRA.lastLog: lightly_encode_output("nada", logs=True),
            DRA.status: "PASS",
        },
    },
    square: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.lastLog: {
                # since execution REJECTS for 0, expect last log for this case to be None
                (i,): lightly_encode_output(i * i, logs=True) if i else None
                for i in range(100)
            },
            DRA.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
        },
    },
    # swap: {"inputs": [[1, 2], [1, "two"], ["one", 2], ["one", "two"]]},
    # string_mult: {"inputs": [["xyzw", i] for i in range(100)]},
    # oldfac: {"inputs": [[i] for i in range(25)]},
}


@pytest.mark.parametrize("mode", [Mode.Signature, Mode.Application])
@pytest.mark.parametrize("subr", SCENARIOS.keys() if SEMANTIC_TESTING else [])
def test_semantic(subr: SubroutineFnWrapper, mode: Mode):
    case_name = subr.name()
    scenario = SCENARIOS[subr]
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
    algod = algod_with_assertion()

    drbuilder = (
        DryRunHelper.build_simple_app_request
        if mode == Mode.Application
        else DryRunHelper.build_simple_lsig_request
    )
    inputs = scenario["inputs"]
    dryrun_reqs = list(map(lambda a: drbuilder(teal, lightly_encode_args(a)), inputs))
    dryrun_resps = list(map(algod.dryrun, dryrun_reqs))

    assertions = scenario.get("assertions", {})
    for i, type_n_assertion in enumerate(assertions.items()):
        assert_type, assertion = type_n_assertion

        if not mode_has_assertion(mode, assert_type):
            print(f"Skipping assert_type {assert_type} for {mode}")
            continue

        assertion = SequenceAssertion(assertion)
        print(
            f"{i+1}. Semantic assertion for {case_name}-{mode}: {assert_type} <<{assertion}>>"
        )
        dryrun_assert(inputs, dryrun_resps, assert_type, assertion)
    # kmd, algod = get_clients()


# if __name__ == "__main__":
#     test_semantic(oldfac)
#     test_semantic(swap)
#     test_semantic(string_mult)
