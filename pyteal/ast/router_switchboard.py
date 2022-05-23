from dataclasses import dataclass
from pyteal.ast.subroutine import (
    ABIReturnSubroutine,
    SubroutineFnWrapper,
)
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
import pyteal as pt

# router_switchboard.py outlines an approach attempting to meet these constraints:
# * Use existing Subroutine abstractions.
# * Limit the amount of input validation required to produce ARC-4 compliant output.
#
# Out of scope:
# Create special-purpose decorators for ARC-4 entry point definition + registration.  Though it's possible to imagine extending the approach and/or providing a parallel _router_ construct.


# BareAppCalls deliberately provides the least-feature rich possible API.  It makes no attempt to define specific behaviors (e.g. creator can update).
#
# Instead, it's up to the caller to specify the desired behavior.  Additionally, it's possible to imagine defiining specific `Subroutine`s as a way to predefine behaviors.
@dataclass(frozen=True)
class BareAppCalls:
    close_out: SubroutineFnWrapper
    clear_state: SubroutineFnWrapper
    delete_application: SubroutineFnWrapper
    no_op: SubroutineFnWrapper
    opt_in: SubroutineFnWrapper
    update_application: SubroutineFnWrapper


# Switchboard exposes a way to build the AST provided ARC-4 Contract inputs.
class Switchboard:
    @staticmethod
    def _validate_bare_app_calls(bac: BareAppCalls) -> None:
        # Imagine validation raising an error when:
        # * a parameter list length > 0
        # * a return value != none
        # Aside:  Can imagine adding a decorator like @router.bare_app_call to isolate the validation logic.
        pass

    @staticmethod
    def _validate_methods(ms: set[ABIReturnSubroutine]) -> None:
        # Imagine validation raising an error when non-ABI parameter exists
        pass

    # new_ast requires _all_ inputs at construction rather than allowing a builder
    # pattern.  Doing so, limits validation cases.
    @staticmethod
    def new_ast(
        app_name: str, bare_app_calls: BareAppCalls, methods: set[ABIReturnSubroutine]
    ) -> Expr:
        Switchboard._validate_bare_app_calls(bare_app_calls)
        Switchboard._validate_methods(methods)

        # Build AST

        return Int(1)


# Usage


@pt.Subroutine(return_type=pt.TealType.none)
def bare_approval() -> pt.Expr:
    return pt.Approve()


@pt.Subroutine(return_type=pt.TealType.none)
def bare_approval_by_creator() -> pt.Expr:
    return pt.Return(pt.Txn.sender() == pt.Global.creator_address())


@pt.Subroutine(return_type=pt.TealType.none)
def bare_reject() -> pt.Expr:
    return pt.Reject()


@pt.ABIReturnSubroutine
def sum(x: pt.abi.Uint64, y: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(x.get() + y.get())


print(
    pt.compileTeal(
        ast=Switchboard.new_ast(
            app_name="my_1st_app",
            bare_app_calls=BareAppCalls(
                close_out=bare_approval,
                clear_state=bare_approval,
                delete_application=bare_approval_by_creator,
                no_op=bare_reject,
                opt_in=bare_approval,
                update_application=bare_approval_by_creator,
            ),
            methods={
                sum,
            },
        ),
        mode=pt.Mode.Application,
        version=6,
    )
)
