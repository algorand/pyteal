.. _atomic_transfer:

Atomic Transfer
===============

`Atomic Transfer <https://developer.algorand.org/docs/atomic-transfers>`_ are irreducible batch transactions
that allow groups of transactions to be submitted at one time.
If any of the transactions fail, then all the transactions will fail.
PyTeal uses :code:`Gtxn` operator to access transactions in an atomic transfer.
For example: ::

  Gtxn.sender(1)

gets the sender of the second (Atomic Transfers are 0 indexed) transaction in the atomic transaction group.

List of :code:`Gtxn` operators:

=================================== ======================= =======================================================================
Operator                            Type                    Notes
=================================== ======================= =======================================================================
:code:`Gtxn.sender(n)`              :code:`TealType.bytes`  32 byte address
:code:`Gtxn.fee(n)`                 :code:`TealType.uint64` in microAlgos
:code:`Gtxn.first_valid(n)`         :code:`TealType.uint64` round number 
:code:`Gtxn.first_valid_time(n)`    :code:`TealType.uint64` causes program to fail, reserved for future use
:code:`Gtxn.last_valid(n)`          :code:`TealType.uint64` round number
:code:`Gtxn.note(n)`                :code:`TealType.bytes`
:code:`Gtxn.lease(n)`               :code:`TealType.bytes`
:code:`Gtxn.receiver(n)`            :code:`TealType.bytes`  32 byte address
:code:`Gtxn.amount(n)`              :code:`TealType.uint64` in microAlgos
:code:`Gtxn.close_remainder_to(n)`  :code:`TealType.bytes`  32 byte address
:code:`Gtxn.vote_pk(n)`             :code:`TealType.bytes`  32 byte address
:code:`Gtxn.selection_pk(n)`        :code:`TealType.bytes`  32 byte address
:code:`Gtxn.vote_first(n)`          :code:`TealType.uint64`
:code:`Gtxn.vote_last(n)`           :code:`TealType.uint64`
:code:`Gtxn.vote_key_dilution(n)`   :code:`TealType.uint64`
:code:`Gtxn.type(n)`                :code:`TealType.bytes`
:code:`Gtxn.type_enum(n)`           :code:`TealType.uint64` see table below
:code:`Gtxn.xfer_asset(n)`          :code:`TealType.uint64` asset ID
:code:`Gtxn.asset_amount(n)`        :code:`TealType.uint64` value in Asset's units
:code:`Gtxn.asset_sender(n)`        :code:`TealType.bytes`  32 byte address, causes clawback of all value if sender is the Clawback
:code:`Gtxn.asset_receiver(n)`      :code:`TealType.bytes`  32 byte address
:code:`Gtxn.asset_close_to(n)`      :code:`TealType.bytes`  32 byte address
:code:`Gtxn.group_index(n)`         :code:`TealType.uint64` position of this transaction within a transaction group
:code:`Gtxn.tx_id(n)`               :code:`TealType.bytes`  the computed ID for this transaction, 32 bytes
=================================== ======================= =======================================================================

where :code:`n >= 0 && n < 16`. 

