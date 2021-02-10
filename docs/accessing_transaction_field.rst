.. _transaction-fields:

Transaction Fields and Global Parameters
========================================

PyTeal smart contracts can access properties of the current transaction and the state of the
blockchain when they are running.

Transaction Fields
------------------

Information about the current transaction being evaluated can be obtained using the :any:`Txn`
object. Below are the PyTeal expressions that refer to transaction fields:

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
:code:`Txn.application_args`              :code:`TealType.bytes[]` Array of application arguments
:code:`Txn.accounts`                      :code:`TealType.bytes[]` Array of additional application accounts
========================================= ======================== =======================================================================

Transaction Type
~~~~~~~~~~~~~~~~

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

Tranasction Array Fields
~~~~~~~~~~~~~~~~~~~~~~~~

Some of the exposed transaction fields are arrays with the type :code:`TealType.bytes[]`. These
fields are :code:`Txn.application_args` and :code:`Txn.accounts`.

The length of these array fields can be found using the :code:`.length()` method, and individual
items can be accesses using bracket notation. For example:

.. code-block:: python

  Txn.application_args.length() # get the number of application arguments in the transaction
  Txn.application_args[0] # get the first application argument
  Txn.application_args[1] # get the second application argument

Special case: :code:`Txn.accounts`
""""""""""""""""""""""""""""""""""

The :code:`Txn.accounts` is a special case array. Normal arrays in PyTeal are :code:`0`-indexed, but
this one is :code:`1`-indexed with a special value at index :code:`0`, the sender's address. That
means if :code:`Txn.accounts.length()` is 2, then indexes :code:`0`, :code:`1`, and :code:`2` will
be present. In fact, :code:`Txn.accounts[0]` will always evaluate to the sender's address, even when
:code:`Txn.accounts.length()` is :code:`0`.

Atomic Tranfer Groups
---------------------

`Atomic Transfers <https://developer.algorand.org/docs/features/atomic_transfers/>`_ are irreducible
batch transactions that allow groups of transactions to be submitted at one time. If any of the
transactions fail, then all the transactions will fail. PyTeal allows programs to access information
about the transactions in an atomic transfer group using the :any:`Gtxn` object. This object acts
like a list of :any:`TxnObject`, meaning all of the above transaction fields on :code:`Txn` are
available on the elements of :code:`Gtxn`. For example:

.. code-block:: python

  Gtxn[0].sender() # get the sender of the first transaction in the atomic transfer group
  Gtxn[1].receiver() # get the receiver of the second transaction in the atomic transfer group

:code:`Gtxn` is zero-indexed and the maximum size of an atomic transfer group is 16. The size of the
current transaction group is available as :any:`Global.group_size()`. A standalone transaction will
have a group size of :code:`1`.

To find the current transaction's index in the transfer group, use :code:`Txn.group_index()`. If the
current transaction is standalone, it's group index will be :code:`0`.

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
:any:`Global.group_size()`              :code:`TealType.uint64` number of txns in this atomic transaction group, at least 1
:any:`Global.logic_sig_version()`       :code:`TealType.uint64` the maximum supported TEAL version
:any:`Global.round()`                   :code:`TealType.uint64` the current round number
:any:`Global.latest_timestamp()`        :code:`TealType.uint64` the latest confirmed block UNIX timestamp
:any:`Global.current_application_id()`  :code:`TealType.uint64` the ID of the current application executing
======================================= ======================= ============================================================
