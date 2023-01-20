.. _opup:

OpUp:  Budget Increase Utility
=================================

Some opcode budget is consumed during execution of every Algorand Smart Contract because every TEAL
instruction has a corresponding cost. In order for the evaluation to succeed, the budget consumed must not
exceed the budget provided. This constraint may introduce a problem for expensive contracts that quickly
consume the initial budget of 700. The OpUp budget increase utility provides a workaround using NoOp inner
transactions that increase the transaction group's pooled compute budget. The funding for issuing the inner
transactions is provided by the contract doing the issuing, not the user calling the contract, so the
contract must have enough funds for this purpose. Note that there is a context specific limit to the number
of inner transactions issued in a transaction group so budget cannot be increased arbitrarily. The available
budget when using the OpUp utility will need to be high enough to execute the TEAL code that issues the inner
transactions. A budget of ~20 is enough for most use cases. 

The default behavior for fees on Inner Transactions is to first take any excess fee credit from overpayment of fees
in the group transaction and, if necessary, draw the remainder of fees from the application account. 
This behavior can be changed by specifying the source that should be used to cover fees by passing a fee source argument. 


Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mode
----

The :any:`pyteal.OpUp` utility is available in two modes: :any:`Explicit` and :any:`OnCall`:

================= ===================================================================================
OpUp Mode         Description
================= ===================================================================================
:code:`Explicit`  Calls a user provided external app when more budget is requested.
:code:`OnCall`    Creates and immediately deletes the app to be called when more budget is requested.
================= ===================================================================================


:any:`Explicit` has the benefit of constructing more lightweight inner transactions, but requires the
target app ID to be provided in the foreign apps array field of the transaction and the :any:`pyteal.OpUp`
constructor in order for it to be accessible. :any:`OnCall` is easier to use, but has slightly more overhead
because the target app must be created and deleted during the evaluation of an app call.

Fee Source
----------

The source of fees to cover the Inner Transactions for the :any:`pyteal.OpUp` utility can be specified by passing the appropriate
argument for the fee source.

==================== ========================================================================================
OpUp Fee Source      Description
==================== ========================================================================================
:code:`GroupCredit`  Only take from the group transaction excess fees
:code:`AppAccount`   Always pay out of the app accounts algo balance
:code:`Any`          Default behavior. First take from GroupCredit then, if necessary, take from App Account.
==================== ========================================================================================


Ensure Budget
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:any:`pyteal.OpUp.ensure_budget` attempts to ensure that the available budget is at least the budget requested by
the caller. If there aren't enough funds for issuing the inner transactions or the inner transaction limit
is exceeded, the evaluation will fail. The typical usage pattern is to insert the :any:`pyteal.OpUp.ensure_budget`
call just before a particularly heavyweight subroutine or expression. Keep in mind that the required budget
expression will be evaluated before the inner transactions are issued so it may be prudent to avoid expensive
expressions, which may exhaust the budget before it can be increased.

In the example below, the :py:meth:`pyteal.Ed25519Verify` expression is used, which costs 1,900.

.. code-block:: python

    # The application id to be called when more budget is requested. This should be
    # replaced with an id provided by the developer.
    target_app_id = Int(1)

    # OnCall mode works the exact same way, just omit the target_app_id
    opup = OpUp(OpUpMode.Explicit, target_app_id)
    program = Seq(
        If(Txn.application_id() != Int(0)).Then(
            Seq(
                opup.ensure_budget(Int(2000)),
                Assert(Ed25519Verify(args[0], args[1], args[2])),
            )
        ),
        Approve(),
    )

Maximize Budget
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:any:`pyteal.OpUp.maximize_budget` attempts to issue as many inner transactions as possible with the given fee.
This essentially maximizes the available budget while putting a ceiling on the amount of fee spent. Just
as with :any:`pyteal.OpUp.ensure_budget`, the evaluation will fail if there aren't enough funds for issuing the
inner transactions or the inner transaction limit is exceeded. This method may be preferred to
:any:`pyteal.OpUp.ensure_budget` when the fee spent on increasing budget needs to be capped or if the developer
would rather just maximize the available budget instead of doing in depth cost analysis on the program.

In the example below, the fee is capped at 3,000 microAlgos for increasing the budget. This works out to 3 inner
transactions being issued, each increasing the available budget by ~700.

.. code-block:: python

    target_app_id = Int(1) # the application id to be called when more budget is requested

    # OnCall mode works the exact same way, just omit the target_app_id
    opup = OpUp(OpUpMode.Explicit, target_app_id)
    program = Seq(
        If(Txn.application_id() != Int(0)).Then(
            Seq(
                opup.maximize_budget(Int(3000)),
                Assert(Ed25519Verify(args[0], args[1], args[2])),
            )
        ),
        Approve(),
    )

If budget increase requests appear multiple times in the program, it may be a good idea to wrap the
invocation in a PyTeal Subroutine to improve code reuse and reduce the size of the compiled program.