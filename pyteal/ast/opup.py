from pyteal.ast.app import OnComplete
from .while_ import While
from .expr import Expr
from .global_ import Global
from .seq import Seq
from .if_ import If
from .int import Int
from .bytes import Bytes
from .gitxn import Gitxn
from .itxn import InnerTxnBuilder
from .txn import TxnField, TxnType, Txn
from enum import Enum


class OpUpMode(Enum):
    """An Enum object that defines the mode used for the OpUp utility.
       
       Note: the Explicit and OnCreate modes require the app id to be provided
       through the foreign apps array.
    """

    """The app to call must be provided by the user."""
    Explicit = 0

    """The app to call is created/deleted when the main app is created/deleted."""
    OnCreate = 1

    """The app to call is created then deleted for each request to increase budget."""
    OnCall = 2


NoOpApp = Bytes("byte 0x068101") # teal program "int 1" assembled


class OpUp():
    """Utility for increasing opcode budget during app execution.
    
    Example:
        .. code-block:: python

            # only the OnCreate mode requires a call to opup.setup()
            opup = OpUp(OpUpMode.OnCreate)
            program_with_opup = Seq(
                opup.setup(),
                ...,
                opup.execute(Int(1000))
                ...,
            )
    """

    def __init__(self, mode: OpUpMode, target_app_id: Expr = None):
        if mode == OpUpMode.Explicit:
            assert target_app_id != None
            self.target_app_id = target_app_id
        elif mode == OpUpMode.OnCreate:
            self.target_app_id = Global.current_application_id + Int(1)

        self.mode = mode

    def _create_app(self) -> Expr:
        create_app_expr = Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.approval_program: NoOpApp,
                    TxnField.clear_state_program: NoOpApp,
                }
            ),
            InnerTxnBuilder.Submit(),
        )

        if self.mode == OpUpMode.OnCall:
            self.target_app_id = Gitxn[0].created_application_id
            return Seq(
                create_app_expr,
                self.target_app_id,
            )

        return create_app_expr

    def _begin(self) -> Expr:
        return If(Global.current_application_id == Int(0)).Then(
            self._create_app()
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

    def _end(self) -> Expr:
        return If(Txn.on_completion() == OnComplete.DeleteApplication).Then(
            self._delete_app(self.target_app_id)
        )

    # setup() should only be used in OnCreate mode
    def setup(self) -> Expr:
        assert(self.mode == OpUpMode.OnCreate)
        return Seq(
            self._begin(),
            self._end(),
        )

    def _opup_expr(self, required_budget: Expr) -> Expr:
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

    def execute(self, required_budget: Expr) -> Expr:
        if self.mode == OpUpMode.OnCall:
            return If(Global.opcode_budget() < required_budget).Then(
                Seq(
                    self._create_app(),
                    self._opup_expr(required_budget),
                    self._delete_app(),
                ))

        return self._opup_expr(required_budget)