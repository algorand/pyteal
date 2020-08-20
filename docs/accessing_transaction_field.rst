.. _transaction-fields:

Transaction Fields and Global Parameters
========================================

PyTeal smart contracts can access properties of the current transaction and the state of the
blockchain when they are running.

Transaction Fields
------------------

Information about the current transaction being evaluated can be obtained using the :any:`Txn`
object. Blow are the PyTeal expressions that refer to transaction fields:

========================================= ======================== =======================================================================
Operator                                  Type                     Notes
========================================= ======================== =======================================================================
:code:`Txn.sender()`                      :code:`TealType.bytes`   32 byte address
:code:`Txn.fee()`                         :code:`TealType.uint64`  in microAlgos
:code:`Txn.first_valid()`                 :code:`TealType.uint64`  round number 
:code:`Txn.last_valid()`                  :code:`TealType.uint64`  round number
:code:`Txn.note()`                        :code:`TealType.bytes`   transaction note in bytes
:code:`Txn.lease()`                       :code:`TealType.bytes`   transaction lease in bytes
:code:`Txn.receiver()`                    :code:`TealType.bytes`   32 byte address
:code:`Txn.amount()`                      :code:`TealType.uint64`  in microAlgos
:code:`Txn.close_remainder_to()`          :code:`TealType.bytes`   32 byte address
:code:`Txn.vote_pk()`                     :code:`TealType.bytes`   32 byte address
:code:`Txn.selection_pk()`                :code:`TealType.bytes`   32 byte address
:code:`Txn.vote_first()`                  :code:`TealType.uint64`
:code:`Txn.vote_last()`                   :code:`TealType.uint64`
:code:`Txn.vote_key_dilution()`           :code:`TealType.uint64`
:code:`Txn.type()`                        :code:`TealType.bytes`
:code:`Txn.type_enum()`                   :code:`TealType.uint64`  see table below
:code:`Txn.xfer_asset()`                  :code:`TealType.uint64`  asset ID
:code:`Txn.asset_amount()`                :code:`TealType.uint64`  value in Asset's units
:code:`Txn.asset_sender()`                :code:`TealType.bytes`   32 byte address, causes clawback of all value if sender is the Clawback
:code:`Txn.asset_receiver()`              :code:`TealType.bytes`   32 byte address
:code:`Txn.asset_close_to()`              :code:`TealType.bytes`   32 byte address
:code:`Txn.group_index()`                 :code:`TealType.uint64`  position of this transaction within a transaction group
:code:`Txn.tx_id()`                       :code:`TealType.bytes`   the computed ID for this transaction, 32 bytes
:code:`Txn.application_id()`              :code:`TealType.uint64`
:code:`Txn.on_completion()`               :code:`TealType.uint64`
:code:`Txn.approval_program()`            :code:`TealType.bytes`
:code:`Txn.clear_state_program()`         :code:`TealType.bytes`
:code:`Txn.rekey_to()`                    :code:`TealType.bytes`   32 byte address
:code:`Txn.config_asset()`                :code:`TealType.uint64`
:code:`Txn.config_asset_total()`          :code:`TealType.uint64`
:code:`Txn.config_asset_decimals()`       :code:`TealType.uint64`
:code:`Txn.config_asset_default_frozen()` :code:`TealType.uint64`
:code:`Txn.config_asset_unit_name()`      :code:`TealType.bytes`
:code:`Txn.config_asset_name()`           :code:`TealType.bytes`
:code:`Txn.config_asset_url()`            :code:`TealType.bytes`
:code:`Txn.config_asset_metadata_hash()`  :code:`TealType.bytes`
:code:`Txn.config_asset_manager()`        :code:`TealType.bytes`   32 byte address
:code:`Txn.config_asset_reserve()`        :code:`TealType.bytes`   32 byte address
:code:`Txn.config_asset_freeze()`         :code:`TealType.bytes`   32 byte address
:code:`Txn.config_asset_clawback()`       :code:`TealType.bytes`   32 byte address
:code:`Txn.freeze_asset()`                :code:`TealType.uint64`
:code:`Txn.freeze_asset_account()`        :code:`TealType.bytes`   32 byte address
:code:`Txn.freeze_asset_frozen()`         :code:`TealType.uint64`
:code:`Txn.application_args()`            :code:`TealType.bytes[]`
:code:`Txn.accounts()`                    :code:`TealType.bytes[]`
========================================= ======================== =======================================================================

The :code:`Txn.type_enum()` values can be checked using the :any:`TxnType` enum:

============================== =============== ============ ========================= 
Value                          Numerical Value Type String  Description
============================== =============== ============ =========================
:any:`TxnType.Unknown`         :code:`0`       unkown       unknown type, invalid
:any:`TxnType.Payment`         :code:`1`       pay          payment
:any:`TxnType.KeyRegistration` :code:`2`       keyreg       key registration
:any:`TxnType.AssetConfig`     :code:`3`       acfg         asset config
:any:`TxnType.AssetTransfer`   :code:`4`       axfer        asset transfer
:any:`TxnType.AssetFreeze`     :code:`5`       afrz         asset freeze
:any:`TxnType.ApplicationCall` :code:`6`       appl         application call
============================== =============== ============ =========================

Atomic Tranfers
~~~~~~~~~~~~~~~

`Atomic Transfers <https://developer.algorand.org/docs/features/atomic_transfers/>`_ are irreducible
batch transactions that allow groups of transactions to be submitted at one time. If any of the
transactions fail, then all the transactions will fail. PyTeal allows programs to access information
about the transactions in an atomic transfer group using the :any:`Gtxn` object. This object acts
like a list of :any:`TxnObject`, meaning all of the above transaction fields on :code:`Txn` are
available on the elements of :code:`Gtxn`. For example:

.. code-block:: python

  Gtxn[0].sender() # get the sender of the first transaction in the atomic transfer group
  Gtxn[1].receiver() # get the receiver of the second transaction in the atomic transfer group

:code:`Gtxn` is zero-indexed and the maximum size of an atomic transfer group is 16.

Global Parameters
-----------------

Information about the current state of the blockchain can be obtained using the following
:any:`Global` expressions:

======================================= ======================= ============================================================
Operator                                Type                    Notes
======================================= ======================= ============================================================
:any:`Global.min_txn_fee()`             :code:`TealType.uint64` in microAlgos  
:any:`Global.min_balance()`             :code:`TealType.uint64` in mircoAlgos
:any:`Global.max_txn_life()`            :code:`TealType.uint64` number of rounds
:any:`Global.zero_address()`            :code:`TealType.bytes`  32 byte address of all zero bytes
:any:`Global.group_size()`              :code:`TealType.uint64` number of txns in this atomic transaction group, At least 1
:any:`Global.logic_sig_version()`       :code:`TealType.uint64` the maximum supported TEAL version
:any:`Global.round()`                   :code:`TealType.uint64` the current round number
:any:`Global.latest_timestamp()`        :code:`TealType.uint64` the latest confirmed block UNIX timestamp
:any:`Global.current_application_id()`  :code:`TealType.uint64` the ID of the current application executing
======================================= ======================= ============================================================
