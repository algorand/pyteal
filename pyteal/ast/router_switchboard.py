from dataclasses import dataclass
from pyteal.ast.subroutine import (
    ABIReturnSubroutine,
    SubroutineFnWrapper,
)
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from typing import Optional
import pyteal as pt

# router_switchboard.py outlines an approach attempting to meet these constraints:
# * Use existing Subroutine abstractions.
# * Limit the amount of input validation required to produce ARC-4 compliant output.
#
# Out of scope:
# Create special-purpose decorators for ARC-4 entry point definition + registration.  Though it's possible to imagine extending the approach and/or providing a parallel _router_ construct.


@dataclass(frozen=True)
class BareAppCall:
    on_create: Optional[SubroutineFnWrapper]
    on_call: Optional[SubroutineFnWrapper]

    @staticmethod
    def none() -> "BareAppCall":
        return BareAppCall(None, None)

    @staticmethod
    def only_on_create(f: SubroutineFnWrapper) -> "BareAppCall":
        return BareAppCall(f, None)

    @staticmethod
    def only_on_call(f: SubroutineFnWrapper) -> "BareAppCall":
        return BareAppCall(None, f)

    @staticmethod
    def always(f: SubroutineFnWrapper) -> "BareAppCall":
        return BareAppCall(f, f)


# BareAppCallSpecification deliberately provides the least-feature rich possible API.  It makes no attempt to define specific behaviors (e.g. creator can update).
#
# Instead, it's up to the caller to specify the desired behavior.  Additionally, it's possible to imagine defiining specific `Subroutine`s as a way to predefine behaviors.
@dataclass(frozen=True)
class BareAppCallSpecification:
    close_out: BareAppCall
    clear_state: BareAppCall
    delete_application: BareAppCall
    no_op: BareAppCall
    opt_in: BareAppCall
    update_application: BareAppCall


# Switchboard exposes a way to build the AST provided ARC-4 Contract inputs.
class Switchboard:
    @staticmethod
    def _validate_bare_app_calls(bacs: BareAppCallSpecification) -> None:
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
        app_name: str, bacs: BareAppCallSpecification, methods: set[ABIReturnSubroutine]
    ) -> Expr:
        Switchboard._validate_bare_app_calls(bacs)
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
            bacs=BareAppCallSpecification(
                close_out=BareAppCall.none(),
                clear_state=BareAppCall.only_on_call(bare_approval_by_creator),
                delete_application=BareAppCall.only_on_create(bare_approval_by_creator),
                no_op=BareAppCall.always(bare_reject),
                opt_in=BareAppCall.always(bare_approval),
                update_application=BareAppCall.only_on_call(bare_approval_by_creator),
            ),
            methods={
                sum,
            },
        ),
        mode=pt.Mode.Application,
        version=6,
    )
)
