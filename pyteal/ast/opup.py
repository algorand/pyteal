from pyteal.ast.app import OnComplete
from pyteal.errors import TealInputError
from .while_ import While
from .expr import Expr
from .global_ import Global
from .seq import Seq
from .if_ import If
from .int import Int
from .bytes import Bytes
from .gitxn import Gitxn
from .itxn import InnerTxnBuilder
from .scratch import ScratchSlot
from .scratchvar import ScratchVar
from .txn import TxnField, TxnType
from .for_ import For
from ..types import TealType, require_type
from enum import Enum


class OpUpMode(Enum):
    """An Enum object that defines the mode used for the OpUp utility.

    Note: the Explicit mode requires the app id to be provided
    through the foreign apps array.
    """

    """The app to call must be provided by the user."""
    Explicit = 0

    """The app to call is created then deleted for each request to increase budget."""
    OnCall = 1


ON_CALL_APP = Bytes("base16", "06810143")  # v6 pyteal program "Int(1)"


class OpUp:
    """Utility for increasing opcode budget during app execution.

    Example:
        .. code-block:: python

            opup = OpUp(OpUpMode.OnCall)
            program_with_opup = Seq(
                ...,
                opup.ensure_budget(Int(1000)),
                ...,
            )
    """

    def __init__(self, mode: OpUpMode, target_app_id: Expr = None):
        if mode == OpUpMode.Explicit:
            if target_app_id is None:
                raise TealInputError(
                    "target_app_id must be specified in Explicit OpUp mode"
                )
            require_type(target_app_id, TealType.uint64)
            self.target_app_id = target_app_id
        elif mode == OpUpMode.OnCall:
            self.target_app_id_slot = ScratchSlot()
        else:
            raise TealInputError("Invalid OpUp mode provided")

        self.mode = mode

        # A budget buffer is necessary to deal with an edge case of ensure_budget():
        #   if the current budget is equal to or only slightly higher than the
        #   required budget then it's possible for ensure_budget() to return with a
        #   current budget less than the required budget. The buffer prevents this
        #   from being the case.
        self.buffer = Int(50)

    def _create_app(self) -> Expr:
        self.target_app_id = self.target_app_id_slot.load()
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.approval_program: ON_CALL_APP,
                    TxnField.clear_state_program: ON_CALL_APP,
                }
            ),
            InnerTxnBuilder.Submit(),
            self.target_app_id_slot.store(Gitxn[0].created_application_id()),
        )

    def _delete_app(self, app_id: Expr) -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.on_completion: OnComplete.DeleteApplication,
                    TxnField.application_id: app_id,
                }
            ),
            InnerTxnBuilder.Submit(),
        )

    def _ensure_budget_expr(self, required_budget: Expr) -> Expr:
        return While(Global.opcode_budget() < required_budget).Do(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.ApplicationCall,
                        TxnField.application_id: self.target_app_id,
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        )

    def ensure_budget(self, required_budget: Expr) -> Expr:
        """Ensure that the budget will be at least the required_budget."""
        require_type(required_budget, TealType.uint64)

        buffered_budget = required_budget + self.buffer
        if self.mode == OpUpMode.OnCall:
            return If(Global.opcode_budget() < buffered_budget).Then(
                Seq(
                    self._create_app(),
                    self._ensure_budget_expr(buffered_budget),
                    self._delete_app(self.target_app_id),
                )
            )

        return self._ensure_budget_expr(buffered_budget)

    def _maximize_budget_expr(self, fee: Expr) -> Expr:
        i = ScratchVar(TealType.uint64)
        n = fee / Int(1000)
        return For(i.store(Int(0)), i.load() < n, i.store(i.load() + Int(1))).Do(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.ApplicationCall,
                        TxnField.application_id: self.target_app_id,
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        )

    def maximize_budget(self, fee: Expr) -> Expr:
        """Maximize the available opcode budget without spending more than the given fee."""
        require_type(fee, TealType.uint64)

        if self.mode == OpUpMode.OnCall:
            return Seq(
                self._create_app(),
                self._maximize_budget_expr(fee),
                self._delete_app(self.target_app_id),
            )

        return self._maximize_budget_expr(fee)


OpUp.__module__ = "pyteal"
