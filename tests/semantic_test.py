from base64 import b64decode
from dataclasses import dataclass
from enum import Enum
from glom import glom
from pathlib import Path
from tabulate import tabulate
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, final

import pytest

from algosdk.testing.dryrun import Helper as DryRunHelper
from algosdk.testing.dryrun import assert_error, assert_no_error

from .semantic_asserts import (
    e2e_teal,
    algod_with_assertion,
    lightly_encode_args,
    lightly_encode_output,
)

from pyteal import *

# TODO: these assertions belong in PySDK
from inspect import signature


@dataclass
class TealVal:
    i: int = 0
    b: str = ""
    is_b: bool = None
    hide_empty: bool = True

    @classmethod
    def from_stack(cls, d: dict) -> "TealVal":
        return TealVal(d["uint"], d["bytes"], d["type"] == 1, hide_empty=False)

    @classmethod
    def from_scratch(cls, d: dict) -> "TealVal":
        return TealVal(d["uint"], d["bytes"], len(d["bytes"]) > 0)

    def is_empty(self) -> bool:
        return not (self.i or self.b)

    def __str__(self) -> str:
        if self.hide_empty and self.is_empty():
            return ""

        assert self.is_b is not None, f"can't handle StackVariable with empty type"
        return "0x" + b64decode(self.b).hex() if self.is_b else str(self.i)

    def as_python_type(self) -> Union[int, str, None]:
        if self.is_b is None:
            return None
        return self.b if self.is_b else self.i


@dataclass
class BlackBoxResults:
    steps_executed: int
    program_counters: List[int]
    teal_line_numbers: List[int]
    teal_source_lines: List[str]
    stack_evolution: List[list]
    scratch_evolution: List[dict]
    final_scratch_state: Dict[int, TealVal]
    slots_used: List[int]
    raw_stacks: List[list]

    def assert_well_defined(self):
        assert all(
            self.steps_executed == len(x)
            for x in (
                self.program_counters,
                self.teal_source_lines,
                self.stack_evolution,
                self.scratch_evolution,
            )
        ), f"some mismatch in trace sizes: all expected to be {self.steps_executed}"

    def __str__(self) -> str:
        return f"BlackBoxResult(steps_executed={self.steps_executed})"

    def steps(self) -> int:
        return self.steps_executed

    def final_stack(self) -> str:
        return self.stack_evolution[-1]

    def final_stack_top(self) -> Union[int, str, None]:
        final_stack = self.raw_stacks[-1]
        if not final_stack:
            return None
        top = final_stack[-1]
        return str(top) if top.is_b else top.i

    def final_scratch(
        self, with_formatting: bool = False
    ) -> Dict[Union[int, str], Union[int, str]]:
        unformatted = {
            i: str(s) if s.is_b else s.i for i, s in self.final_scratch_state.items()
        }
        if not with_formatting:
            return unformatted
        return {f"S@{i:03}": s for i, s in unformatted.items()}

    def slots(self) -> List[int]:
        return self.slots_used

    def final_as_row(self) -> Dict[str, Union[str, int]]:
        return {
            "steps": self.steps(),
            "top_of_stack": self.final_stack_top(),
            **self.final_scratch(with_formatting=True),
        }


class DryRunTester:
    def __init__(
        self,
        name: str,
        dry_run_response: dict,
        runner_address: str,
        default_txn_index: int = 0,
        col_max: int = None,
        scratch_colon: str = "->",
        scratch_verbose: bool = False,
    ):
        self.name = name
        self.resp = dry_run_response
        self.runner_address = runner_address
        self.default_report_idx = default_txn_index
        self.col_max = col_max
        self.scratch_colon = scratch_colon
        self.scratch_verbose = scratch_verbose

        self.black_box_results = [
            scrape_the_black_box(
                tx["app-call-trace"],
                tx["disassembly"],
                scratch_colon=self.scratch_colon,
            )
            for tx in self.resp["txns"]
        ]
        for bbr in self.black_box_results:
            bbr.assert_well_defined()

    ### methods that pivot of testing idx ###
    def testing_txn(self, idx: int = None) -> dict:
        if idx is None:
            idx = self.default_report_idx
        return self.resp["txns"][idx]

    def cost(self, idx: int = None) -> int:
        return self.testing_txn(idx)["cost"]

    def last_log(self, idx: int = None) -> Optional[str]:
        if idx is None:
            idx = self.default_report_idx
        logs = self.logs(idx)
        return b64decode(logs[-1]).hex() if logs else None

    def logs(self, idx: int = None) -> List[str]:
        if idx is None:
            idx = self.default_report_idx
        return self.resp["txns"][idx].get("logs", [])

    def get_black_box_result(self, idx: int = None) -> BlackBoxResults:
        if idx is None:
            idx = self.default_report_idx
        return self.black_box_results[idx]

    def last_stack_value(self, idx: int = None) -> Optional[TealVal]:
        last_stack = self.get_black_box_result(idx).raw_stacks[-1]
        return last_stack[-1] if last_stack else None

    def max_stack_height(self, idx: int = None) -> Tuple[int, List[int]]:
        stacks = self.get_black_box_result(idx).raw_stacks
        max_height = max(map(len, stacks))
        lines = [i + 1 for i, s in enumerate(stacks) if len(s) == max_height]
        return max_height, lines

    def slots_used(self, idx: int = None) -> Set[int]:
        return self.get_black_box_result(idx).slots_used

    def final_scratch_state(self, idx: int = None) -> Dict[int, TealVal]:
        return self.get_black_box_result(idx).final_scratch_state

    def _global_x_used(self, x: str, idx: int = None) -> int:
        gdeltas = self.testing_txn(idx).get("global-delta", [])
        return len(
            [gd for gd in gdeltas if glom(gd, f"value.{x}", default=False) is not False]
        )

    def global_bytes_used(self, idx: int = None) -> int:
        return self._global_x_used("bytes", idx)

    def global_uints_used(self, idx: int = None) -> int:
        return self._global_x_used("uint", idx)

    def _local_x_used(self, x: str, idx: int = None) -> int:
        """Not sure this is correct"""
        ldeltas = [
            ld
            for ld in self.testing_txn(idx).get("local-deltas", [])
            if ld["address"] == self.runner_address
        ]
        if not ldeltas:
            return 0
        assert len(ldeltas) == 1
        ldelta = ldeltas[0]["delta"]
        return len(
            [ld for ld in ldelta if glom(ld, f"value.{x}", default=False) is not False]
        )

    def local_bytes_used(self, idx: int = None) -> int:
        return self._local_x_used("bytes", idx)

    def local_uints_used(self, idx: int = None) -> int:
        return self._local_x_used("uint", idx)

    ### human readable reporting ###

    def report(self, unique_index: int = None) -> str:
        if unique_index is not None:
            prev_index = self.default_report_idx
            self.default_report_idx = unique_index
        max_stack_height, msh_lines = self.max_stack_height()
        bookend = f"""
        <<<<<<{self.name}>>>>>>
REPORTS FOR {len(self.resp["txns"])} TRANSACTIONS
TRANSACTION INDEX (for this short summary): {self.default_report_idx}
BLACK BOX RESULT: {self.get_black_box_result()}
TOTAL OP-CODE COST: {self.cost()}
MAXIMUM STACK HEIGHT: {max_stack_height} AT LINES {msh_lines}
TOP OF STACK: {self.last_stack_value()!r}
FINAL LOG: {self.last_log()}
{len(self.slots_used())} SLOTS USED: {self.slots_used()}
FINAL SCRATCH STATE: {self.final_scratch_state()}
GLOBAL BYTES USED: {self.global_bytes_used()}
GLOBAL UINTS USED: {self.global_uints_used()}
LOCAL BYTES USED: {self.local_bytes_used()}
LOCAL UINTS USED: {self.local_uints_used()}
        <<<<<<{self.name}>>>>>>"""

        txn_reports = []
        for i, txn in enumerate(self.resp["txns"]):
            if unique_index is not None and i != unique_index:
                continue
            txn_reports.append(self.txn_report(i, txn, self.col_max))

        txn_reports = [bookend] + txn_reports + [bookend]

        if unique_index is not None:
            self.default_report_idx = prev_index

        return "\n".join(txn_reports)

    def txn_report(
        self,
        idx: int,
        txn: dict,
        col_max: int,
    ) -> str:
        gdelta = txn.get("global-delta", [])
        ldelta = txn.get("local-deltas", [])

        app_messages = txn["app-call-messages"]
        app_trace = txn["app-call-trace"]
        cost = txn["cost"]
        app_lines = txn["disassembly"]

        lsig_lines = txn["logic-sig-disassembly"]
        lsig_messages = txn["logic-sig-messages"]
        lsig_trace = txn["logic-sig-trace"]

        app_table = deprecated_table(
            app_trace,
            app_lines,
            col_max,
            scratch_colon=self.scratch_colon,
            scratch_verbose=self.scratch_verbose,
        )
        lsig_table = deprecated_table(
            lsig_trace,
            lsig_lines,
            col_max,
            scratch_colon=self.scratch_colon,
            scratch_verbose=self.scratch_verbose,
        )

        return f"""===============
        <<<Transaction@index={idx}>>>
===============
TOTAL COST: {cost}
===============
txn.app_call_rejected={app_messages[-1] != 'PASS'}
txn.logic_sig_rejected={lsig_messages[-1] != 'PASS'}
===============
App Messages: {app_messages}
App Logs: {self.logs(idx)}
App Trace: (with max column size {col_max})
{app_table}
===============
Lsig Messages: {lsig_messages}
Lsig Trace: (with max column size {col_max})
{lsig_table}
===============
Global Delta:
{gdelta}
===============
Local Delta:
{ldelta}
"""


def deprecated_table(
    trace: List[dict],
    lines: List[str],
    col_max: int,
    scratch_colon: str = "->",
    scratch_verbose: bool = False,
    scratch_before_stack: bool = True,
) -> str:
    assert not (
        scratch_verbose and scratch_before_stack
    ), "Cannot request scratch columns before stack when verbose"

    black_box_result = scrape_the_black_box(
        trace,
        lines,
        scratch_colon=scratch_colon,
        scratch_verbose=scratch_verbose,
    )

    return make_table(
        black_box_result,
        col_max,
        scratch_verbose=scratch_verbose,
        scratch_before_stack=scratch_before_stack,
    )


def make_table(
    black_box_result: BlackBoxResults,
    col_max: int,
    scratch_verbose: bool = False,
    scratch_before_stack: bool = True,
):
    assert not (
        scratch_verbose and scratch_before_stack
    ), "Cannot request scratch columns before stack when verbose"

    def empty_hack(se):
        return se if se else [""]

    rows = [
        list(
            map(
                str,
                [
                    i + 1,
                    black_box_result.program_counters[i],
                    black_box_result.teal_line_numbers[i],
                    black_box_result.teal_source_lines[i],
                    black_box_result.stack_evolution[i],
                    *empty_hack(black_box_result.scratch_evolution[i]),
                ],
            )
        )
        for i in range(black_box_result.steps_executed)
    ]
    if col_max and col_max > 0:
        rows = [[x[:col_max] for x in row] for row in rows]
    headers = [
        "step",
        "PC#",
        "L#",
        "Teal",
        "Stack",
        *(
            [f"S@{s}" for s in black_box_result.slots_used]
            if scratch_verbose
            else ["Scratch"]
        ),
    ]
    if scratch_before_stack:
        # with assertion above, we know that there is only one
        # scratch column and it's at the very end
        headers[-1], headers[-2] = headers[-2], headers[-1]
        for i in range(len(rows)):
            rows[i][-1], rows[i][-2] = rows[i][-2], rows[i][-1]

    table = tabulate(rows, headers=headers, tablefmt="presto")
    return table


def scrape_the_black_box(
    trace, lines, scratch_colon: str = "->", scratch_verbose: bool = False
) -> BlackBoxResults:
    pcs = [t["pc"] for t in trace]
    line_nums = [t["line"] for t in trace]

    def line_or_err(i, ln):
        line = lines[ln - 1]
        err = trace[i].get("error")
        return err if err else line

    tls = [line_or_err(i, ln) for i, ln in enumerate(line_nums)]
    N = len(pcs)
    assert N == len(tls), f"mismatch of lengths in pcs v. tls ({N} v. {len(tls)})"

    # process stack var's
    raw_stacks = [
        [TealVal.from_stack(s) for s in x] for x in [t["stack"] for t in trace]
    ]
    stacks = [f"[{', '.join(map(str,stack))}]" for stack in raw_stacks]
    assert N == len(
        stacks
    ), f"mismatch of lengths in tls v. stacks ({N} v. {len(stacks)})"

    # process scratch var's
    scratches = [
        [TealVal.from_scratch(s) for s in x]
        for x in [t.get("scratch", []) for t in trace]
    ]
    scratches = [
        {i: s for i, s in enumerate(scratch) if not s.is_empty()}
        for scratch in scratches
    ]
    slots_used = sorted(set().union(*(s.keys() for s in scratches)))
    final_scratch_state = scratches[-1]
    if not scratch_verbose:

        def compute_delta(prev, curr):
            pks, cks = set(prev.keys()), set(curr.keys())
            new_keys = cks - pks
            if new_keys:
                return {k: curr[k] for k in new_keys}
            return {k: v for k, v in curr.items() if prev[k] != v}

        scratch_deltas = [scratches[0]]
        for i in range(1, len(scratches)):
            scratch_deltas.append(compute_delta(scratches[i - 1], scratches[i]))

        scratches = [
            [f"{i}{scratch_colon}{v}" for i, v in scratch.items()]
            for scratch in scratch_deltas
        ]
    else:
        scratches = [
            [
                f"{i}{scratch_colon}{scratch[i]}" if i in scratch else ""
                for i in slots_used
            ]
            for scratch in scratches
        ]

    assert N == len(
        scratches
    ), f"mismatch of lengths in tls v. scratches ({N} v. {len(scratches)})"

    bbr = BlackBoxResults(
        N,
        pcs,
        line_nums,
        tls,
        stacks,
        scratches,
        final_scratch_state,
        slots_used,
        raw_stacks,
    )
    bbr.assert_well_defined()
    return bbr


class SequenceAssertion:
    def __init__(
        self,
        predicate: Union[Dict[Tuple, Union[str, int]], Callable],
        enforce: bool = False,
        name: str = None,
    ):
        self.definition = predicate
        self.predicate, self._expected = self.prepare_predicate(predicate)
        self.enforce = enforce
        self.name = name

    def __repr__(self):
        return f"SequenceAssertion({self.definition})"[:100]

    def __call__(self, args: list, actual: Union[str, int]) -> Tuple[bool, str]:
        assertion = self.predicate(args, actual)
        msg = ""
        if not assertion:
            msg = f"SequenceAssertion for '{self.name}' failed for for args {args}: actual is [{actual}] BUT expected [{self.expected(args)}]"
            if self.enforce:
                assert assertion, msg

        return assertion, msg

    def expected(self, args: list) -> Union[str, int]:
        return self._expected(args)

    @classmethod
    def prepare_predicate(cls, predicate):
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

        # N == 1:
        return lambda args, actual: predicate(args) == actual, lambda args: predicate(
            args
        )


DryRunAssertionType = Enum(
    "DryRunAssertionType",
    "cost lastLog finalScratch stackTop maxStackHeight status rejected passed error noError globalStateHas localStateHas",
)
DRA = DryRunAssertionType


def mode_has_assertion(mode: Mode, assertion_type: DryRunAssertionType) -> bool:
    missing = {
        Mode.Signature: {DryRunAssertionType.cost, DryRunAssertionType.lastLog},
        Mode.Application: set(),
    }
    if assertion_type in missing[mode]:
        return False

    return True


def dig_actual(
    dryrun_resp: dict, assert_type: DryRunAssertionType, assertion_arg: Any = None
) -> Union[str, int, bool]:
    txns = dryrun_resp["txns"]
    assert len(txns) == 1, f"expecting exactly 1 transaction but got {len(txns)}"
    txn = txns[0]
    mode = Mode.Signature if "logic-sig-messages" in txn else Mode.Application
    is_app = mode == Mode.Application

    assert mode_has_assertion(
        mode, assert_type
    ), f"{mode} cannot handle dig information from txn for assertion type {assert_type}"
    is_app = mode == Mode.Application

    if assert_type == DryRunAssertionType.cost:
        return txn["cost"]

    if assert_type == DryRunAssertionType.lastLog:
        last_log = txn.get("logs", [None])[-1]
        if last_log is None:
            return last_log
        return b64decode(last_log).hex()

    if assert_type == DryRunAssertionType.finalScratch:
        trace = extract_trace(txn, is_app)
        lines = extract_lines(txn, is_app)
        bbr = scrape_the_black_box(trace, lines)
        return {k: v.as_python_type() for k, v in bbr.final_scratch_state.items()}

    if assert_type == DryRunAssertionType.stackTop:
        trace = extract_trace(txn, is_app)
        stack = trace[-1]["stack"]
        if not stack:
            return None
        tv = TealVal.from_scratch(stack[-1])
        return tv.as_python_type()

    if assert_type == DryRunAssertionType.maxStackHeight:
        trace = extract_trace(txn, is_app)
        stack = trace[-1]["stack"]
        return max(len(s) for s in stack)

    if assert_type == DryRunAssertionType.status:
        return extract_status(mode, txn)

    if assert_type == DryRunAssertionType.rejected:
        return extract_status(mode, txn) == "REJECT"

    if assert_type == DryRunAssertionType.passed:
        return extract_status(mode, txn) == "PASS"

    if assert_type == DryRunAssertionType.error:
        return assert_error(dryrun_resp, pattern=assertion_arg) is None

    if assert_type == DryRunAssertionType.noError:
        return assert_no_error(dryrun_resp) is None

    raise Exception(f"Unknown assert_type {assert_type}")


def extract_logs(txn):
    return txn.get("logs", [])


def extract_cost(txn):
    return txn.get("cost")


def extract_status(mode, txn):
    return (
        txn["logic-sig-messages"][-1]
        if mode == Mode.Signature
        else txn["app-call-messages"][-1]
    )


def extract_lines(txn, is_app):
    return txn["disassembly" if is_app else "logic-sig-disassembly"]


def extract_trace(txn, is_app):
    return txn["app-call-trace" if is_app else "logic-sig-trace"]


def extract_messages(txn, is_app):
    return txn["app-call-messages" if is_app else "logic-sig-messages"]


def extract_local_deltas(txn):
    return txn.get("local-deltas", [])


def extract_global_delta(txn):
    return txn.get("global-delta", [])


def extract_all(txn: dict, is_app: bool) -> dict:
    trace = extract_trace(txn, is_app)
    lines = extract_lines(txn, is_app)
    bbr = scrape_the_black_box(trace, lines)

    return {
        "cost": extract_cost(txn),
        "logs": extract_logs(txn),
        "gdelta": extract_global_delta(txn),
        "ldeltas": extract_local_deltas(txn),
        "messages": extract_messages(txn, is_app),
        "trace": trace,
        "lines": lines,
        "bbr": bbr,
    }


def txn_as_row(txn: dict, is_app: bool) -> dict:
    extracts = extract_all(txn, is_app)
    logs = extracts["logs"]
    return {
        "cost": extracts["cost"],
        "final_log": logs[-1] if logs else None,
        "final_message": extracts["messages"][-1],
        **extracts["bbr"].final_as_row(),
    }


def dryrun_assert(
    inputs: List[list],
    dryrun_resps: List[dict],
    assert_type: DryRunAssertionType,
    test: SequenceAssertion,
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
        is_app = mode == Mode.Application

        actual = dig_actual(resp, assert_type)
        ok, msg = test(args, actual)
        if not ok:
            extracts = extract_all(txn, is_app)
            cost = extracts["cost"]
            logs = extracts["logs"]
            gdelta = extracts["gdelta"]
            ldelta = extracts["ldeltas"]
            messages = extracts["messages"]
            bbr = extracts["bbr"]
            table = make_table(bbr, -1)

            assert ok, f"""===============
{msg}
===============
App Trace:
{table}
===============
MODE: {mode}
TOTAL COST: {cost}
===============
txn.app_call_rejected={messages[-1] != 'PASS'}
===============
Messages: {messages}
Logs: {logs}
===============
-----{bbr}-----
TOTAL STEPS: {bbr.steps()}
FINAL STACK: {bbr.final_stack()}
FINAL STACK TOP: {bbr.final_stack_top()}
FINAL SCRATCH: {bbr.final_scratch()}
SLOTS USED: {bbr.slots()}
FINAL AS ROW: {bbr.final_as_row()}
===============
Global Delta:
{gdelta}
===============
Local Delta:
{ldelta}
===============
{msg}
===============
TXN AS ROW: {txn_as_row(txn, is_app)}
"""


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


def expected_contained(expected, actual):
    for k, v in expected.items():
        if k not in actual or v != actual[k]:
            return False
    return True


def fac(n):
    if n < 2:
        return 1
    return n * fac(n - 1)


SCENARIOS = {
    exp: {
        "inputs": [[]],
        "assertions": {
            DRA.cost: 11,
            DRA.finalScratch: lambda _, actual: not actual or actual == {0: 1024},
            DRA.lastLog: lightly_encode_output(2 ** 10, logs=True),
            DRA.stackTop: 1024,
            DRA.maxStackHeight: 3,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    square_byref: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.cost: lambda _, actual: 20 < actual < 22,
            DRA.finalScratch: lambda args, actual: (
                args[0] ** 2 in actual.values() if args[0] else True
            ),
            DRA.lastLog: lightly_encode_output(1337, logs=True),
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 3,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    square: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.cost: 14,
            DRA.lastLog: {
                # since execution REJECTS for 0, expect last log for this case to be None
                (i,): lightly_encode_output(i * i, logs=True) if i else None
                for i in range(100)
            },
            DRA.stackTop: lambda args: args[0] ** 2,
            DRA.maxStackHeight: 3,
            DRA.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRA.passed: lambda i: i[0] > 0,
            DRA.rejected: lambda i: i[0] == 0,
            DRA.noError: True,
        },
    },
    swap: {"inputs": [[1, 2], [1, "two"], ["one", 2], ["one", "two"]]},
    string_mult: {"inputs": [["xyzw", i] for i in range(100)]},
    oldfac: {
        "inputs": [[i] for i in range(25)],
        "assertions": {DRA.stackTop: lambda args: fac(args[0])},
    },
}

SCENARIOS = {oldfac: SCENARIOS[oldfac]}


@pytest.mark.parametrize("mode", [Mode.Signature, Mode.Application])
@pytest.mark.parametrize("subr", SCENARIOS.keys() if SEMANTIC_TESTING else [])
def test_semantic(subr: SubroutineFnWrapper, mode: Mode):
    path = Path.cwd() / "tests" / "teal"
    case_name = subr.name()
    scenario = SCENARIOS[subr]
    assert isinstance(subr, SubroutineFnWrapper), f"unexpected subr type {type(subr)}"
    print(f"semantic e2e test of {case_name}")
    approval = e2e_teal(subr, mode)
    teal = compileTeal(approval(), mode, version=6, assembleConstants=True)
    path /= f'{"lsig" if mode == Mode.Signature else "app"}_{case_name}.teal'
    with open(path, "w") as f:
        f.write(teal)
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

        assertion = SequenceAssertion(
            assertion, name=f"{case_name}[{i}]@{mode}-{assert_type}"
        )
        print(
            f"{i+1}. Semantic assertion for {case_name}-{mode}: {assert_type} <<{assertion}>>"
        )
        dryrun_assert(inputs, dryrun_resps, assert_type, assertion)


# if __name__ == "__main__":
#     test_semantic(oldfac)
#     test_semantic(swap)
#     test_semantic(string_mult)
