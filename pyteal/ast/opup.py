from pyteal.ast.app import OnComplete
from pyteal.errors import TealInputError
from pyteal.ast.while_ import While
from pyteal.ast.expr import Expr
from pyteal.ast.global_ import Global
from pyteal.ast.seq import Seq
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.itxn import InnerTxnBuilder
from pyteal.ast.scratchvar import ScratchVar
from pyteal.ast.txn import TxnField, TxnType
from pyteal.ast.for_ import For
from pyteal.types import TealType, require_type
from enum import Enum


class OpUpMode(Enum):
    """An Enum object that defines the mode used for the OpUp utility.

    Note: the Explicit mode requires the app id to be provided
    through the foreign apps array in order for it to be accessible
    during evaluation.
    """

    # The app to call must be provided by the user.
    Explicit = 0

    # The app to call is created then deleted for each request to increase budget.
    OnCall = 1


ON_CALL_APP = Bytes("base16", "068101")  # v6 teal program "int 1"
MIN_TXN_FEE = Int(1000)


class OpUp:
    """Utility for increasing opcode budget during app execution.

    Requires TEAL version 6 or higher.

    Example:
        .. code-block:: python

            # OnCall mode: doesn't accept target_app_id as an argument
            opup = OpUp(OpUpMode.OnCall)
            program_with_opup = Seq(
                ...,
                opup.ensure_budget(Int(1000)),
                ...,
            )

            # Explicit mode: requires target_app_id as an argument
            opup = OpUp(OpUpMode.Explicit, Int(1))
            program_with_opup = Seq(
                ...,
                opup.ensure_budget(Int(1000)),
                ...,
            )
    """

    def __init__(self, mode: OpUpMode, target_app_id: Expr = None):
        """Create a new OpUp object.

        Args:
            mode: OpUpMode that determines the style of budget increase
                to use. See the OpUpMode Enum for more information.
            target_app_id (optional): In Explicit mode, the OpUp utility
                requires the app_id to target for inner app calls. Defaults
                to None.
        """

        # With only OnCall and Explicit modes supported, the mode argument
        # isn't strictly necessary but it will most likely be required if
        # we do decide to add more modes in the future.
        if mode == OpUpMode.Explicit:
            if target_app_id is None:
                raise TealInputError(
                    "target_app_id must be specified in Explicit OpUp mode"
                )
            require_type(target_app_id, TealType.uint64)
            self.target_app_id = target_app_id
        elif mode == OpUpMode.OnCall:
            if target_app_id is not None:
                raise TealInputError("target_app_id is not used in OnCall OpUp mode")
        else:
            raise TealInputError("Invalid OpUp mode provided")

        self.mode = mode

    def _construct_itxn(self) -> Expr:
        if self.mode == OpUpMode.Explicit:
            return Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.ApplicationCall,
                        TxnField.application_id: self.target_app_id,
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        else:
            return Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.ApplicationCall,
                        TxnField.on_completion: OnComplete.DeleteApplication,
                        TxnField.approval_program: ON_CALL_APP,
                        TxnField.clear_state_program: ON_CALL_APP,
                    }
                ),
                InnerTxnBuilder.Submit(),
            )

    def ensure_budget(self, required_budget: Expr) -> Expr:
        """Ensure that the budget will be at least the required_budget.

        Note: the available budget just prior to calling ensure_budget() must be
        high enough to execute the budget increase code. The exact budget required
        depends on the provided required_budget expression, but a budget of ~20
        should be sufficient for most use cases. If lack of budget is an issue then
        consider moving the call to ensure_budget() earlier in the pyteal program."""
        require_type(required_budget, TealType.uint64)

        # A budget buffer is necessary to deal with an edge case of ensure_budget():
        #   if the current budget is equal to or only slightly higher than the
        #   required budget then it's possible for ensure_budget() to return with a
        #   current budget less than the required budget. The buffer prevents this
        #   from being the case.
        buffer = Int(10)
        buffered_budget = ScratchVar(TealType.uint64)
        return Seq(
            buffered_budget.store(required_budget + buffer),
            While(buffered_budget.load() > Global.opcode_budget()).Do(
                self._construct_itxn()
            ),
        )

    def maximize_budget(self, fee: Expr) -> Expr:
        """Maximize the available opcode budget without spending more than the given fee.

        Note: the available budget just prior to calling maximize_budget() must be
        high enough to execute the budget increase code. The exact budget required
        depends on the provided fee expression, but a budget of ~25 should be
        sufficient for most use cases. If lack of budget is an issue then consider
        moving the call to maximize_budget() earlier in the pyteal program."""
        require_type(fee, TealType.uint64)

        i = ScratchVar(TealType.uint64)
        n = fee / Global.min_txn_fee()
        return For(i.store(Int(0)), i.load() < n, i.store(i.load() + Int(1))).Do(
            self._construct_itxn()
        )


OpUp.__module__ = "pyteal"
