.. _examples:

PyTeal Examples
===============

Here are some additional PyTeal example programs:

Signature Mode
--------------

Atomic Swap
~~~~~~~~~~~~~~~

*Atomic Swap* allows the transfer of Algos from a buyer to a seller in exchange for a good or
service. This is done using a *Hashed Time Locked Contract*. In this scheme, the buyer and funds a
TEAL account with the sale price. The buyer also picks a secret value and encodes a secure hash of
this value in the TEAL program. The TEAL program will transfer its balance to the seller if the
seller is able to provide the secret value that corresponds to the hash in the program. When the
seller renders the good or service to the buyer, the buyer discloses the secret from the program.
The seller can immediately verify the secret and withdraw the payment.

.. literalinclude:: ../examples/atomic_swap.py
    :language: python

Split Payment
~~~~~~~~~~~~~

*Split Payment* splits payment between :code:`tmpl_rcv1` and :code:`tmpl_rcv2` on the ratio of
:code:`tmpl_ratn / tmpl_ratd`.

.. literalinclude:: ../examples/split.py
    :language: python

Periodic Payment
~~~~~~~~~~~~~~~~

*Periodic Payment* allows some account to execute periodic withdrawal of funds. This PyTeal program
creates an contract account that allows :code:`tmpl_rcv` to withdraw :code:`tmpl_amt` every
:code:`tmpl_period` rounds for :code:`tmpl_dur` after every multiple of :code:`tmpl_period`.

After :code:`tmpl_timeout`, all remaining funds in the escrow are available to :code:`tmpl_rcv`.

.. literalinclude:: ../examples/periodic_payment.py
    :language: python

Application Mode
----------------

Voting
~~~~~~

*Voting* allows accounts to register and vote for arbitrary candidates. Here a *candidate* is any byte
slice and anyone is allowed to register to vote.

This example has a configurable *registration period* defined by the global state :code:`RegBegin`
and :code:`RegEnd` which restrict when accounts can register to vote. There is also a separate
configurable *voting period* defined by the global state :code:`VotingBegin` and :code:`VotingEnd`
which restrict when voting can take place.

An account must register in order to vote. Accounts cannot vote more than once, and if an account
opts out of the application before the voting period has concluded, their vote is discarded. The
results are visible in the global state of the application, and the winner is the candidate with the
highest number of votes.

.. literalinclude:: ../examples/vote.py
    :language: python

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

.. literalinclude:: ../examples/asset.py
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

.. literalinclude:: ../examples/security_token.py
    :language: python
