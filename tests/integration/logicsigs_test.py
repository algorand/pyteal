from itertools import product
from pathlib import Path
import pytest

from pyteal import compileTeal, Mode

import examples.signature.factorizer_game as factorizer

from tests.blackbox_asserts import algod_with_assertion
from graviton.blackbox import (
    DryRunExecutor as Executor,
    DryRunInspector as Inspector,
    DryRunProperty as DRProp,
)
from graviton.invariant import Invariant

REPORTS_DIR = Path.cwd() / "tests" / "integration" / "reports"
ALGOD = algod_with_assertion()

COEFFICIENTS = [(1, 5, 7)]


def inputs_for_coefficients(a, b, q):
    return product(range(20), range(20))


def poly_4(x):
    return abs(x**2 - 12 * x + 35)


def naive_prize(x, y):
    return 1_000_000 * max(10 - (sum(map(poly_4, (x, y))) + 1) // 2, 0)


def payment_amount(x, y):
    return 0 if x == y else naive_prize(x, y)


@pytest.mark.parametrize("a, p, q", COEFFICIENTS)
def test_factorizer_game(a: int, p: int, q: int):
    compiled = compileTeal(
        factorizer.logicsig(a, p, q),
        version=6,
        mode=Mode.Signature,
        assembleConstants=True,
    )
    inputs = list(inputs_for_coefficients(a, p, q))
    N = len(inputs)
    amts = list(map(lambda args: payment_amount(*args), inputs))

    inspectors, txns = [], []
    for args, amt in zip(inputs, amts):
        txn = {"amt": amt}
        txns.append(txn)
        inspectors.append(Executor.dryrun_logicsig(ALGOD, compiled, args, **txn))

    print(
        f"generating a report for (a,p,q) = {a,p,q} with {N} dry-run calls and spreadsheet rows"
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
        f"validate procedurally that payment amount as expected for (a,p,q) = {a,p,q} over {N} dry-run calls"
    )

    for args, inspector in zip(inputs, inspectors):
        x, y = args
        eprize = naive_prize(x, y)
        assert inspector.final_scratch().get(3, 0) == eprize, inspector.report(
            args, f"final scratch slot #3 {x, y}"
        )
