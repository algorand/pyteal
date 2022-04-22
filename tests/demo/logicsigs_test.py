from itertools import product
from os import environ
from pathlib import Path
import pytest

from pyteal import compileTeal, Mode

import examples.signature.factorizer_game as factorizer

from utils.blackbox import algod_client
from graviton.blackbox import (
    DryRunExecutor as Executor,
    DryRunInspector as Inspector,
    DryRunProperty as DRProp,
)
from graviton.invariant import Invariant

REPORTS_DIR = Path.cwd() / "tests" / "integration" / "reports"
ALGOD = algod_client()


def get_params_from_environ():
    A, P, Q, M, N = list(map(lambda x: int(environ.get(x)), ("A", "P", "Q", "M", "N")))
    return A, P, Q, M, N


def get_factorizer_param_sequence():
    A, P, Q, M, N = get_params_from_environ()
    return [(a, p, q, M, N) for a in range(A) for p in range(P) for q in range(Q)]


def inputs_for_coefficients(a, p, q, M, N):
    # TODO: this should really be focused around the roots p and q
    return product(range(M), range(N))


def factorizer_game_check(a: int, p: int, q: int, M: int, N: int):
    ae = None
    if a <= 0 or p < 0 or q <= p:
        with pytest.raises(AssertionError) as ae:
            factorizer.logicsig(a, p, q),

    if ae:
        return

    compiled = compileTeal(
        factorizer.logicsig(a, p, q),
        version=6,
        mode=Mode.Signature,
        assembleConstants=True,
    )
    inputs = list(inputs_for_coefficients(a, p, q, M, N))
    N = len(inputs)

    def poly(x):
        return abs(a * x**2 - a * (p + q) * x + a * p * q)

    def naive_prize(x, y):
        return 1_000_000 * max(10 - (sum(map(poly, (x, y))) + 1) // 2, 0)

    def payment_amount(x, y):
        return 0 if x == y else naive_prize(x, y)

    amts = list(map(lambda args: payment_amount(*args), inputs))

    inspectors, txns = [], []
    for args, amt in zip(inputs, amts):
        txn = {"amt": amt}
        txns.append(txn)
        inspectors.append(Executor.dryrun_logicsig(ALGOD, compiled, args, **txn))

    print(
        f"generating a report for (a,p,q) = {a,p,q} with {M, N} dry-run calls and spreadsheet rows"
    )
    filebase = f"factorizer_game_{a}_{p}_{q}"
    csvpath = REPORTS_DIR / f"{filebase}.csv"
    with open(csvpath, "w") as f:
        f.write(Inspector.csv_report(inputs, inspectors, txns=txns))

    print(f"validating passing_invariant for (a,p,q) = {a,p,q} over {N} dry-run calls")
    passing_invariant = Invariant(
        lambda args: bool(payment_amount(*args)),
        name=f"passing invariant for coeffs {a, p, q}",
    )
    passing_invariant.validates(DRProp.passed, inputs, inspectors)

    print(
        f"validate procedurally that payment amount as expected for (a,p,q) = {a,p,q} over {M, N} dry-rundry-run calls"
    )

    for args, inspector in zip(inputs, inspectors):
        x, y = args
        eprize = naive_prize(x, y)
        final_scratches = inspector.final_scratch().values()
        assert eprize == 0 or eprize in final_scratches, inspector.report(
            args,
            f"(a, p, q, x, y) = {a, p, q, x, y}. final scratch slots expected to contain {eprize} v. actual={final_scratches}",
        )


@pytest.mark.parametrize("a, p, q, M, N", get_factorizer_param_sequence())
def test_many_factorizer_games(a: int, p: int, q: int, M: int, N: int):
    factorizer_game_check(a, p, q, M, N)
