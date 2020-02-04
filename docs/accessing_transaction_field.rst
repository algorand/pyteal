.. _transaction-fields:

Transaction Fields and Global Parameters
========================================

A PyTeal expression can be the value of a field of
the current transaction or the value of a global parameter.
Blow are the PyTeal expressions that refer to transaction fields:

================================= ======================= =======================================================================
Operator                          Type                    Notes
================================= ======================= =======================================================================
:code:`Txn.sender()`              :code:`TealType.bytes`  32 byte address
:code:`Txn.fee()`                 :code:`TealType.uint64` in microAlgos
:code:`Txn.first_valid()`         :code:`TealType.uint64` round number 
:code:`Txn.first_valid_time()`    :code:`TealType.uint64` causes program to fail, reserved for future use
:code:`Txn.last_valid()`          :code:`TealType.uint64` round number
:code:`Txn.note()`                :code:`TealType.bytes`
:code:`Txn.lease()`               :code:`TealType.bytes`
:code:`Txn.receiver()`            :code:`TealType.bytes`  32 byte address
:code:`Txn.amount()`              :code:`TealType.uint64` in microAlgos
:code:`Txn.close_remainder_to()`  :code:`TealType.bytes`  32 byte address
:code:`Txn.vote_pk()`             :code:`TealType.bytes`  32 byte address
:code:`Txn.selection_pk()`        :code:`TealType.bytes`  32 byte address
:code:`Txn.vote_first()`          :code:`TealType.uint64`
:code:`Txn.vote_last()`           :code:`TealType.uint64`
:code:`Txn.vote_key_dilution()`   :code:`TealType.uint64`
:code:`Txn.type()`                :code:`TealType.bytes`
:code:`Txn.type_enum()`           :code:`TealType.uint64` see table below
:code:`Txn.xfer_asset()`          :code:`TealType.uint64` asset ID
:code:`Txn.asset_amount()`        :code:`TealType.uint64` value in Asset's units
:code:`Txn.asset_sender()`        :code:`TealType.bytes`  32 byte address, causes clawback of all value if sender is the Clawback
:code:`Txn.asset_receiver()`      :code:`TealType.bytes`  32 byte address
:code:`Txn.asset_close_to()`      :code:`TealType.bytes`  32 byte address
:code:`Txn.group_index()`         :code:`TealType.uint64` position of this transaction within a transaction group
:code:`Txn.tx_id()`               :code:`TealType.bytes`  the computed ID for this transaction, 32 bytes
================================= ======================= =======================================================================

:code:`Txn.type_enum()` values:

============== ============ ========================= 
Value          Type String  Description
============== ============ =========================
:code:`Int(0)` unkown       unknown type, invalid
:code:`Int(1)` pay          payment
:code:`Int(2)` keyreg       key registration
:code:`Int(3)` acfg         asset config
:code:`Int(4)` axfer        asset transfer
:code:`Int(5)` afrz         asset freeze
============== ============ =========================

PyTeal expressions that refer to global parameters:

============================== ======================= ============================================================
Operator                       Type                    Notes
============================== ======================= ============================================================
:code:`Global.min_txn_fee()`   :code:`TealType.uint64` in microAlgos  
:code:`Global.min_balance()`   :code:`TealType.uint64` in mircoAlgos
:code:`Global.max_txn_life()`  :code:`TealType.uint64` number of rounds
:code:`Global.zero_address()`  :code:`TealType.bytes`  32 byte address of all zero bytes
:code:`Global.group_size()`    :code:`TealType.uint64` number of txns in this atomic transaction group, At least 1
============================== ======================= ============================================================


