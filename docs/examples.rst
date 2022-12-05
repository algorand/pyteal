.. _examples:

PyTeal Examples
===============

Here are some additional PyTeal example programs:

Signature Mode
--------------

Atomic Swap
~~~~~~~~~~~~~~~

*Atomic Swap* allows the transfer of Algos from a buyer to a seller in exchange for a good or
service. This is done using a *Hashed Time Locked Contract*. In this scheme, the buyer funds a
TEAL account with the sale price. The buyer also picks a secret value and encodes a secure hash of
this value in the TEAL program. The TEAL program will transfer its balance to the seller if the
seller is able to provide the secret value that corresponds to the hash in the program. When the
seller renders the good or service to the buyer, the buyer discloses the secret from the program.
The seller can immediately verify the secret and withdraw the payment.

.. literalinclude:: ../examples/signature/atomic_swap.py
    :language: python

Split Payment
~~~~~~~~~~~~~

*Split Payment* splits payment between :code:`tmpl_rcv1` and :code:`tmpl_rcv2` on the ratio of
:code:`tmpl_ratn / tmpl_ratd`.

.. literalinclude:: ../examples/signature/split.py
    :language: python

Periodic Payment
~~~~~~~~~~~~~~~~

*Periodic Payment* allows some account to execute periodic withdrawal of funds. This PyTeal program
creates an contract account that allows :code:`tmpl_rcv` to withdraw :code:`tmpl_amt` every
:code:`tmpl_period` rounds for :code:`tmpl_dur` after every multiple of :code:`tmpl_period`.

After :code:`tmpl_timeout`, all remaining funds in the escrow are available to :code:`tmpl_rcv`.

.. literalinclude:: ../examples/signature/periodic_payment.py
    :language: python

Application Mode
----------------

Voting
~~~~~~

*Voting* allows accounts to register and vote for arbitrary choices. Here a *choice* is any byte
slice and anyone is allowed to register to vote.

This example has a configurable *registration period* defined by the global state :code:`RegBegin`
and :code:`RegEnd` which restrict when accounts can register to vote. There is also a separate
configurable *voting period* defined by the global state :code:`VotingBegin` and :code:`VotingEnd`
which restrict when voting can take place.

An account must register in order to vote. Accounts cannot vote more than once, and if an account
opts out of the application before the voting period has concluded, their vote is discarded. The
results are visible in the global state of the application, and the winner is the candidate with the
highest number of votes.

.. literalinclude:: ../examples/application/vote.py
    :language: python

A reference script that deploys the voting application is below:

.. literalinclude:: ../examples/application/vote_deploy.py
    :language: python

Example output for deployment would be:

.. code-block:: bash

    Registration rounds: 592 to 602
    Vote rounds: 603 to 613
    Waiting for confirmation...
    Transaction KXJHR6J4QSCAHO36L77DPJ53CLZBCCSPSBAOGTGQDRA7WECDXUEA confirmed in round 584.
    Created new app-id: 29
    Global state: {'RegEnd': 602, 'VoteBegin': 603, 'VoteEnd': 613, 'Creator': '49y8gDrKSnM77cgRyFzYdlkw18SDVNKhhOiS6NVVH8U=', 'RegBegin': 592}
    Waiting for round 592
    Round 585
    Round 586
    Round 587
    Round 588
    Round 589
    Round 590
    Round 591
    Round 592
    OptIn from account:  FVQEFNOSD25TDBTTTIU2I5KW5DHR6PADYMZESTOCQ2O3ME4OWXEI7OHVRY
    Waiting for confirmation...
    Transaction YWXOAREFSUYID6QLWQHANTXK3NR2XOVTIQYKMD27F3VXJKP7CMYQ confirmed in round 595.
    OptIn to app-id: 29
    Waiting for round 603
    Round 596
    Round 597
    Round 598
    Round 599
    Round 600
    Round 601
    Round 602
    Round 603
    Call from account: FVQEFNOSD25TDBTTTIU2I5KW5DHR6PADYMZESTOCQ2O3ME4OWXEI7OHVRY
    Waiting for confirmation...
    Transaction WNV4DTPEMVGUXNRZHMWNSCUU7AQJOCFTBKJT6NV2KN6THT4QGKNQ confirmed in round 606.
    Local state: {'voted': 'choiceA'}
    Waiting for round 613
    Round 607
    Round 608
    Round 609
    Round 610
    Round 611
    Round 612
    Round 613
    Global state: {'RegBegin': 592, 'RegEnd': 602, 'VoteBegin': 603, 'VoteEnd': 613, 'choiceA': 1, 'Creator': '49y8gDrKSnM77cgRyFzYdlkw18SDVNKhhOiS6NVVH8U='}
    The winner is: choiceA
    Waiting for confirmation...
    Transaction 535KBWJ7RQX4ISV763IUUICQWI6VERYBJ7J6X7HPMAMFNKJPSNPQ confirmed in round 616.
    Deleted app-id: 29
    Waiting for confirmation...
    Transaction Z56HDAJYARUC4PWGWQLCBA6TZYQOOLNOXY5XRM3IYUEEUCT5DRMA confirmed in round 618.
    Cleared app-id: 29

Asset
~~~~~

*Asset* is an implementation of a custom asset type using smart contracts. While Algorand has
`ASAs <https://developer.algorand.org/docs/features/asa/>`_, in some blockchains the only way to
create a custom asset is through smart contracts.

At creation, the creator specifies the total supply of the asset. Initially this supply is placed in
a reserve and the creator is made an admin. Any admin can move funds from the reserve into the
balance of any account that has opted into the application using the *mint* argument. Additionally,
any admin can move funds from any account's balance into the reserve using the *burn* argument.

Accounts are free to transfer funds in their balance to any other account that has opted into the
application. When an account opts out of the application, their balance is added to the reserve.

.. literalinclude:: ../examples/application/asset.py
    :language: python

Security Token
~~~~~~~~~~~~~~

*Security Token* is an extension of the *Asset* example with more features and restrictions. There
are two types of admins, *contract admins* and *transfer admins*.

Contract admins can delete the smart contract if the entire supply is in the reserve. They can
promote accounts to transfer or contract admins. They can also *mint* and *burn* funds.

Transfer admins can impose maximum balance limitations on accounts, temporarily lock accounts,
assign accounts to transfer groups, and impose transaction restrictions between transaction groups.

Both contract and transfer admins can pause trading of funds and freeze individual accounts.

Accounts can only transfer funds if trading is not paused, both the sender and receive accounts are
not frozen or temporarily locked, transfer group restrictions are not in place between them, and the
receiver's account does not have a maximum balance restriction that would be invalidated.

.. literalinclude:: ../examples/application/security_token.py
    :language: python
