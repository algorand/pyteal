from pathlib import Path
import pytest
from typing import Any

from algosdk.transaction import OnComplete
from graviton.abi_strategy import ABIArgsMod, ABICallStrategy, RandomABIStrategyHalfSized
from graviton.blackbox import DryRunEncoder
from graviton.invariant import DryRunProperty as DRProp

import pyteal as pt

NUM_ROUTER_DRYRUNS = 7
FIXTURES = Path.cwd() / "tests" / "integration" / "teal" / "router"


def add_methods_to_router(router: pt.Router):
    @pt.ABIReturnSubroutine
    def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() + b.get())

    meth = router.add_method_handler(add)
    assert meth.method_signature() == "add(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def sub(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() - b.get())

    meth = router.add_method_handler(sub)
    assert meth.method_signature() == "sub(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def mul(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() * b.get())

    meth = router.add_method_handler(mul)
    assert meth.method_signature() == "mul(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def div(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() / b.get())

    meth = router.add_method_handler(div)
    assert meth.method_signature() == "div(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def mod(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() % b.get())

    meth = router.add_method_handler(mod)
    assert meth.method_signature() == "mod(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def all_laid_to_args(
        _a: pt.abi.Uint64,
        _b: pt.abi.Uint64,
        _c: pt.abi.Uint64,
        _d: pt.abi.Uint64,
        _e: pt.abi.Uint64,
        _f: pt.abi.Uint64,
        _g: pt.abi.Uint64,
        _h: pt.abi.Uint64,
        _i: pt.abi.Uint64,
        _j: pt.abi.Uint64,
        _k: pt.abi.Uint64,
        _l: pt.abi.Uint64,
        _m: pt.abi.Uint64,
        _n: pt.abi.Uint64,
        _o: pt.abi.Uint64,
        _p: pt.abi.Uint64,
        *,
        output: pt.abi.Uint64,
    ):
        return output.set(
            _a.get()
            + _b.get()
            + _c.get()
            + _d.get()
            + _e.get()
            + _f.get()
            + _g.get()
            + _h.get()
            + _i.get()
            + _j.get()
            + _k.get()
            + _l.get()
            + _m.get()
            + _n.get()
            + _o.get()
            + _p.get()
        )

    meth = router.add_method_handler(all_laid_to_args)
    assert (
        meth.method_signature()
        == "all_laid_to_args(uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64)uint64"
    )

    @pt.ABIReturnSubroutine
    def empty_return_subroutine() -> pt.Expr:
        return pt.Log(pt.Bytes("appear in both approval and clear state"))

    meth = router.add_method_handler(
        empty_return_subroutine,
        method_config=pt.MethodConfig(
            no_op=pt.CallConfig.CALL,
            opt_in=pt.CallConfig.ALL,
            clear_state=pt.CallConfig.CALL,
        ),
    )
    assert meth.method_signature() == "empty_return_subroutine()void"

    @pt.ABIReturnSubroutine
    def log_1(*, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(1)

    meth = router.add_method_handler(
        log_1,
        method_config=pt.MethodConfig(
            no_op=pt.CallConfig.CALL,
            opt_in=pt.CallConfig.CALL,
            clear_state=pt.CallConfig.CALL,
        ),
    )

    assert meth.method_signature() == "log_1()uint64"

    @pt.ABIReturnSubroutine
    def log_creation(*, output: pt.abi.String) -> pt.Expr:
        return output.set("logging creation")

    meth = router.add_method_handler(
        log_creation, method_config=pt.MethodConfig(no_op=pt.CallConfig.CREATE)
    )
    assert meth.method_signature() == "log_creation()string"

    @pt.ABIReturnSubroutine
    def approve_if_odd(condition_encoding: pt.abi.Uint32) -> pt.Expr:
        return (
            pt.If(condition_encoding.get() % pt.Int(2))
            .Then(pt.Approve())
            .Else(pt.Reject())
        )

    meth = router.add_method_handler(
        approve_if_odd,
        method_config=pt.MethodConfig(
            no_op=pt.CallConfig.NEVER, clear_state=pt.CallConfig.CALL
        ),
    )
    assert meth.method_signature() == "approve_if_odd(uint32)void"


def generate_and_test_routers():
    routers = []

    # V6 not ready for Frame Pointers:
    on_completion_actions = pt.BareCallActions(
        opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes("optin call"))),
        clear_state=pt.OnCompleteAction.call_only(pt.Approve()),
    )
    with pytest.raises(pt.TealInputError) as e:
        pt.Router("will-error", on_completion_actions).compile_program(
            version=6, optimize=pt.OptimizeOptions(frame_pointers=True)
        )
    assert "Frame pointers aren't available" in str(e.value)

    # QUESTIONABLE V6:
    _router_with_oc = pt.Router(
        "ASimpleQuestionablyRobustContract", on_completion_actions
    )
    add_methods_to_router(_router_with_oc)
    (
        actual_ap_with_oc_compiled,
        actual_csp_with_oc_compiled,
        _,
    ) = _router_with_oc.compile_program(version=6)
    with open(FIXTURES / "questionable_approval_v6.teal") as f:
        expected_ap_with_oc = f.read()
    with open(FIXTURES / "questionable_clear_v6.teal") as f:
        expected_csp_with_oc = f.read()
    assert expected_ap_with_oc == actual_ap_with_oc_compiled
    assert expected_csp_with_oc == actual_csp_with_oc_compiled
    routers.append(("questionable", 6, _router_with_oc))

    # YACC V6:
    _router_without_oc = pt.Router("yetAnotherContractConstructedFromRouter")
    add_methods_to_router(_router_without_oc)
    (
        actual_ap_without_oc_compiled,
        actual_csp_without_oc_compiled,
        _,
    ) = _router_without_oc.compile_program(version=6)
    with open(FIXTURES / "yacc_approval_v6.teal") as f:
        expected_ap_without_oc = f.read()
    with open(FIXTURES / "yacc_clear_v6.teal") as f:
        expected_csp_without_oc = f.read()
    assert actual_ap_without_oc_compiled == expected_ap_without_oc
    assert actual_csp_without_oc_compiled == expected_csp_without_oc
    routers.append(("yacc", 6, _router_without_oc))

    # QUESTIONABLE FP V8:
    _router_with_oc = pt.Router(
        "QuestionableRouterGenerateCodeWithFramePointer", on_completion_actions
    )
    add_methods_to_router(_router_with_oc)
    (
        actual_ap_with_oc_compiled,
        actual_csp_with_oc_compiled,
        _,
    ) = _router_with_oc.compile_program(version=8)
    with open(FIXTURES / "questionableFP_approval_v8.teal") as f:
        expected_ap_with_oc = f.read()
    with open(FIXTURES / "questionableFP_clear_v8.teal") as f:
        expected_csp_with_oc = f.read()
    assert actual_ap_with_oc_compiled == expected_ap_with_oc
    assert actual_csp_with_oc_compiled == expected_csp_with_oc
    routers.append(("questionable", 8, _router_with_oc))

    # YACC FP V8:
    _router_without_oc = pt.Router(
        "yetAnotherContractConstructedFromRouterWithFramePointer"
    )
    add_methods_to_router(_router_without_oc)
    (
        actual_ap_without_oc_compiled,
        actual_csp_without_oc_compiled,
        _,
    ) = _router_without_oc.compile_program(version=8)
    with open(FIXTURES / "yaccFP_approval_v8.teal") as f:
        expected_ap_without_oc = f.read()
    with open(FIXTURES / "yaccFP_clear_v8.teal") as f:
        expected_csp_without_oc = f.read()
    assert actual_ap_without_oc_compiled == expected_ap_without_oc
    assert actual_csp_without_oc_compiled == expected_csp_without_oc
    routers.append(("yacc", 8, _router_without_oc))

    return routers


ROUTER_CASES = generate_and_test_routers()

TYPICAL_IAC_OC = (False, OnComplete.NoOpOC)

# LEGEND FOR TEST CASES:
#
# * @0 - method: str. method == `None` indicates bare app call
#
# * @1 - approval_call_types: list[tuple[bool, OncComplete]]
#   [(is_app_create, `OnComplete`), ...] contexts expected for approval program
#
# * @2 - clear_call_types: list[tuple[bool, Oncomplete]]
#   [(is_app_create, `OnComplete`), ...] contexts expected for clear program
#
# * @3 - predicates: dict[DRProp, Any]
#   these are being asserted after being processed into Invariant's
#
# NOTE: the "yacc" routers will simply ignore the case with method `None`
# as they do not have any bare-app-calls
QUESTIONABLE_CASES: list[
    tuple[
        str,
        list[tuple[bool, OnComplete]],
        list[tuple[bool, OnComplete]],
        dict[DRProp, Any],
    ]
] = [
    (
        "add",
        [TYPICAL_IAC_OC],
        [],
        {DRProp.passed: True, DRProp.lastLog: lambda args: args[1] + args[2]},
    ),
    (
        "sub",
        [TYPICAL_IAC_OC],
        [],
        {
            DRProp.passed: lambda args: args[1] >= args[2],
            DRProp.lastLog: (
                lambda args, actual: True
                if args[1] < args[2]
                else actual == args[1] - args[2]
            ),
        },
    ),
    (
        "mul",
        [TYPICAL_IAC_OC],
        [],
        {DRProp.passed: True, DRProp.lastLog: lambda args: args[1] * args[2]},
    ),
    (
        "div",
        [TYPICAL_IAC_OC],
        [],
        {DRProp.passed: True, DRProp.lastLog: lambda args: args[1] // args[2]},
    ),
    (
        "mod",
        [TYPICAL_IAC_OC],
        [],
        {DRProp.passed: True, DRProp.lastLog: lambda args: args[1] % args[2]},
    ),
    (
        "all_laid_to_args",
        [TYPICAL_IAC_OC],
        [],
        {DRProp.passed: True, DRProp.lastLog: lambda args: sum(args[1:])},
    ),
    (
        "empty_return_subroutine",
        [
            (False, OnComplete.NoOpOC),
            (False, OnComplete.OptInOC),
            (True, OnComplete.OptInOC),
        ],
        [
            (False, OnComplete.ClearStateOC),
        ],
        {
            DRProp.passed: True,
            DRProp.lastLog: DryRunEncoder.hex(
                "appear in both approval and clear state"
            ),
        },
    ),
    (
        "log_1",
        [(False, OnComplete.NoOpOC), (False, OnComplete.OptInOC)],
        [
            (False, OnComplete.ClearStateOC),
        ],
        {DRProp.passed: True, DRProp.lastLog: 1},
    ),
    (
        "log_creation",
        [(True, OnComplete.NoOpOC)],
        [],
        {DRProp.passed: True, DRProp.lastLog: "logging creation"},
    ),
    (
        "approve_if_odd",  # this should only appear in the clear-state program
        [],
        [
            (False, OnComplete.ClearStateOC),
        ],
        {
            DRProp.passed: lambda args: args[1] % 2 == 1,
            DRProp.lastLog: None,
        },
    ),
    (
        None,
        [(False, OnComplete.OptInOC)],
        [
            (False, OnComplete.ClearStateOC),
        ],
        {
            DRProp.passed: True,
            DRProp.lastLog: lambda _, actual: actual
            in (None, DryRunEncoder.hex("optin call")),
        },
    ),
]




@pytest.mark.parametrize("case, version, router", ROUTER_CASES)
@pytest.mark.parametrize(
    "method, approval_call_types, clear_call_types, predicates", QUESTIONABLE_CASES
)
def test_abi_router_positive(
    case, version, router, method, approval_call_types, clear_call_types, predicates
):
    """
    Test the _positive_ version of a case. In other words, ensure that for the given:
        * method or bare call
        * OnComplete value
        * number of arguments
    that the app call succeeds according to the provided _invariants_ success definition
    """
    def get_aa_strat(method_runner, abi_args_mod=None) -> ABICallStrategy:
        return ABICallStrategy(
            method_runner.teal,
            method_runner.contract,
            RandomABIStrategyHalfSized,
            num_dryruns=NUM_ROUTER_DRYRUNS,
            abi_args_mod=abi_args_mod,
        )


    # def run_positive(is_approve, method_runner, call_types, invariants):
    good_abi_args = get_aa_strat(method_runner)

    algod = get_algod()

    if not call_types:
        return

    method = method_runner.method
    sim = Simulation(
        algod,
        ExecutionMode.Application,
        method_runner.teal,
        invariants,
        abi_method_signature=good_abi_args.method_signature(method),
        omit_method_selector=False,
        validation=False,
    )

    def msg():
        return f"""
TEST CASE [{method_runner}]({"APPROVAL" if is_approve else "CLEAR"}):
test_function={inspect.stack()[2][3]}
method={method}
is_app_create={is_app_create}
on_complete={on_complete!r}"""

    for is_app_create, on_complete in call_types:
        sim_result = sim.run_and_assert(
            good_abi_args,
            method=method,
            txn_params=TxParams.for_app(
                is_app_create=is_app_create,
                on_complete=on_complete,
            ),
            msg=msg(),
        )
        assert sim_result.succeeded

    # run_positive(True, approval_runner, approval_call_types, invariants)
    # run_positive(False, clear_runner, clear_call_types, invariants)
