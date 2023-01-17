from pathlib import Path
import pytest

import pyteal as pt

FIXTURES = Path.cwd() / "tests" / "integration" / "teal" / "router"


def test_router_app():
    def add_methods_to_router(router: pt.Router):
        @pt.ABIReturnSubroutine
        def add(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() + b.get())

        meth = router.add_method_handler(add)
        assert meth.method_signature() == "add(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def sub(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() - b.get())

        meth = router.add_method_handler(sub)
        assert meth.method_signature() == "sub(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def mul(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() * b.get())

        meth = router.add_method_handler(mul)
        assert meth.method_signature() == "mul(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def div(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() / b.get())

        meth = router.add_method_handler(div)
        assert meth.method_signature() == "div(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def mod(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
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

    on_completion_actions = pt.BareCallActions(
        opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes("optin call"))),
        clear_state=pt.OnCompleteAction.call_only(pt.Approve()),
    )

    with pytest.raises(pt.TealInputError) as e:
        pt.Router("will-error", on_completion_actions).compile_program(
            version=6, optimize=pt.OptimizeOptions(frame_pointers=True)
        )

    assert "Frame pointers aren't available" in str(e.value)

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

    assert expected_ap_with_oc == actual_ap_with_oc_compiled

    with open(FIXTURES / "questionable_clear_v6.teal") as f:
        expected_csp_with_oc = f.read()

    assert expected_csp_with_oc == actual_csp_with_oc_compiled

    _router_without_oc = pt.Router("yetAnotherContractConstructedFromRouter")
    add_methods_to_router(_router_without_oc)
    (
        actual_ap_without_oc_compiled,
        actual_csp_without_oc_compiled,
        _,
    ) = _router_without_oc.compile_program(version=6)

    with open(FIXTURES / "yacc_approval_v6.teal") as f:
        expected_ap_without_oc = f.read()
    assert actual_ap_without_oc_compiled == expected_ap_without_oc

    with open(FIXTURES / "yacc_clear_v6.teal") as f:
        expected_csp_without_oc = f.read()
    assert actual_csp_without_oc_compiled == expected_csp_without_oc

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
    assert actual_ap_with_oc_compiled == expected_ap_with_oc

    with open(FIXTURES / "questionableFP_clear_v8.teal") as f:
        expected_csp_with_oc = f.read()
    assert actual_csp_with_oc_compiled == expected_csp_with_oc

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
    assert actual_ap_without_oc_compiled == expected_ap_without_oc

    with open(FIXTURES / "yaccFP_clear_v8.teal") as f:
        expected_csp_without_oc = f.read()

    assert actual_csp_without_oc_compiled == expected_csp_without_oc
