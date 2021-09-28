.. _transaction-fields:

Transaction Fields and Global Parameters
========================================

PyTeal smart contracts can access properties of the current transaction and the state of the
blockchain when they are running.

Transaction Fields
------------------

Information about the current transaction being evaluated can be obtained using the :any:`Txn`
object. Below are the PyTeal expressions that refer to transaction fields:

================================================================================ ========================= ================ ============================================================================
Operator                                                                         Type                      Min TEAL Version Notes
================================================================================ ========================= ================ ============================================================================
:any:`Txn.sender() <TxnObject.sender>`                                           :code:`TealType.bytes`    2                32 byte address
:any:`Txn.fee() <TxnObject.fee>`                                                 :code:`TealType.uint64`   2                in microAlgos
:any:`Txn.first_valid() <TxnObject.first_valid>`                                 :code:`TealType.uint64`   2                round number 
:any:`Txn.last_valid() <TxnObject.last_valid>`                                   :code:`TealType.uint64`   2                round number
:any:`Txn.note() <TxnObject.note>`                                               :code:`TealType.bytes`    2                transaction note in bytes
:any:`Txn.lease() <TxnObject.lease>`                                             :code:`TealType.bytes`    2                transaction lease in bytes
:any:`Txn.receiver() <TxnObject.receiver>`                                       :code:`TealType.bytes`    2                32 byte address
:any:`Txn.amount() <TxnObject.amount>`                                           :code:`TealType.uint64`   2                in microAlgos
:any:`Txn.close_remainder_to() <TxnObject.close_remainder_to>`                   :code:`TealType.bytes`    2                32 byte address
:any:`Txn.vote_pk() <TxnObject.vote_pk>`                                         :code:`TealType.bytes`    2                32 byte address
:any:`Txn.selection_pk() <TxnObject.selection_pk>`                               :code:`TealType.bytes`    2                32 byte address
:any:`Txn.vote_first() <TxnObject.vote_first>`                                   :code:`TealType.uint64`   2
:any:`Txn.vote_last() <TxnObject.vote_last>`                                     :code:`TealType.uint64`   2
:any:`Txn.vote_key_dilution() <TxnObject.vote_key_dilution>`                     :code:`TealType.uint64`   2
:any:`Txn.nonparticipation() <TxnObject.nonparticipation>`                       :code:`TealType.uint64`   5                Marks an account nonparticipating for rewards
:any:`Txn.type() <TxnObject.type>`                                               :code:`TealType.bytes`    2
:any:`Txn.type_enum() <TxnObject.type_enum>`                                     :code:`TealType.uint64`   2                see table below
:any:`Txn.xfer_asset() <TxnObject.xfer_asset>`                                   :code:`TealType.uint64`   2                ID of asset being transferred
:any:`Txn.asset_amount() <TxnObject.asset_amount>`                               :code:`TealType.uint64`   2                value in Asset's units
:any:`Txn.asset_sender() <TxnObject.asset_sender>`                               :code:`TealType.bytes`    2                32 byte address, causes clawback of all value if sender is the clawback
:any:`Txn.asset_receiver() <TxnObject.asset_receiver>`                           :code:`TealType.bytes`    2                32 byte address
:any:`Txn.asset_close_to() <TxnObject.asset_close_to>`                           :code:`TealType.bytes`    2                32 byte address
:any:`Txn.group_index() <TxnObject.group_index>`                                 :code:`TealType.uint64`   2                position of this transaction within a transaction group, starting at 0
:any:`Txn.tx_id() <TxnObject.tx_id>`                                             :code:`TealType.bytes`    2                the computed ID for this transaction, 32 bytes
:any:`Txn.application_id() <TxnObject.application_id>`                           :code:`TealType.uint64`   2
:any:`Txn.on_completion() <TxnObject.on_completion>`                             :code:`TealType.uint64`   2
:any:`Txn.approval_program() <TxnObject.approval_program>`                       :code:`TealType.bytes`    2
:any:`Txn.clear_state_program() <TxnObject.clear_state_program>`                 :code:`TealType.bytes`    2
:any:`Txn.rekey_to() <TxnObject.rekey_to>`                                       :code:`TealType.bytes`    2                32 byte address
:any:`Txn.config_asset() <TxnObject.config_asset>`                               :code:`TealType.uint64`   2                ID of asset being configured
:any:`Txn.config_asset_total() <TxnObject.config_asset_total>`                   :code:`TealType.uint64`   2
:any:`Txn.config_asset_decimals() <TxnObject.config_asset_decimals>`             :code:`TealType.uint64`   2
:any:`Txn.config_asset_default_frozen() <TxnObject.config_asset_default_frozen>` :code:`TealType.uint64`   2
:any:`Txn.config_asset_unit_name() <TxnObject.config_asset_unit_name>`           :code:`TealType.bytes`    2
:any:`Txn.config_asset_name() <TxnObject.config_asset_name>`                     :code:`TealType.bytes`    2
:any:`Txn.config_asset_url() <TxnObject.config_asset_url>`                       :code:`TealType.bytes`    2
:any:`Txn.config_asset_metadata_hash() <TxnObject.config_asset_metadata_hash>`   :code:`TealType.bytes`    2
:any:`Txn.config_asset_manager() <TxnObject.config_asset_manager>`               :code:`TealType.bytes`    2                32 byte address
:any:`Txn.config_asset_reserve() <TxnObject.config_asset_reserve>`               :code:`TealType.bytes`    2                32 byte address
:any:`Txn.config_asset_freeze() <TxnObject.config_asset_freeze>`                 :code:`TealType.bytes`    2                32 byte address
:any:`Txn.config_asset_clawback() <TxnObject.config_asset_clawback>`             :code:`TealType.bytes`    2                32 byte address
:any:`Txn.freeze_asset() <TxnObject.freeze_asset>`                               :code:`TealType.uint64`   2
:any:`Txn.freeze_asset_account() <TxnObject.freeze_asset_account>`               :code:`TealType.bytes`    2                32 byte address
:any:`Txn.freeze_asset_frozen() <TxnObject.freeze_asset_frozen>`                 :code:`TealType.uint64`   2
:any:`Txn.global_num_uints() <TxnObject.global_num_uints>`                       :code:`TealType.uint64`   3                Maximum global integers in app schema
:any:`Txn.global_num_byte_slices() <TxnObject.global_num_byte_slices>`           :code:`TealType.uint64`   3                Maximum global byte strings in app schema
:any:`Txn.local_num_uints() <TxnObject.local_num_uints>`                         :code:`TealType.uint64`   3                Maximum local integers in app schema
:any:`Txn.local_num_byte_slices() <TxnObject.local_num_byte_slices>`             :code:`TealType.uint64`   3                Maximum local byte strings in app schema
:any:`Txn.extra_program_pages() <TxnObject.extra_program_pages>`                 :code:`TealType.uint64`   4                Number of extra program pages for app
:any:`Txn.application_args <TxnObject.application_args>`                         :code:`TealType.bytes[]`  2                Array of application arguments
:any:`Txn.accounts <TxnObject.accounts>`                                         :code:`TealType.bytes[]`  2                Array of application accounts
:any:`Txn.assets <TxnObject.assets>`                                             :code:`TealType.uint64[]` 3                Array of application assets
:any:`Txn.applications <TxnObject.applications>`                                 :code:`TealType.uint64[]` 3                Array of applications
:any:`InnerTxn.created_asset_id() <TxnObject.created_asset_id>`                  :code:`TealType.uint64`   5                The ID of the newly created asset in this transaction. This is only valid on inner transactions.
:any:`InnerTxn.created_application_id() <TxnObject.created_application_id>`      :code:`TealType.uint64`   5                The ID of the newly created application in this transaction. This is only valid on inner transactions.
:any:`InnerTxn.logs <TxnObject.logs>`                                            :code:`TealType.bytes[]`  5                Array of application logged items. This is only valid on inner transactions.
================================================================================ ========================= ================ ============================================================================

Transaction Type
~~~~~~~~~~~~~~~~

The :any:`Txn.type_enum() <TxnObject.type_enum>` values can be checked using the :any:`TxnType` enum:

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

Transaction Array Fields
~~~~~~~~~~~~~~~~~~~~~~~~

Some of the exposed transaction fields are arrays with the type :code:`TealType.uint64[]` or :code:`TealType.bytes[]`.
These fields are :code:`Txn.application_args`, :code:`Txn.assets`, :code:`Txn.accounts`, :code:`Txn.applications`,
and :code:`InnerTxn.logs`.

The length of these array fields can be found using the :code:`.length()` method, and individual
items can be accesses using bracket notation. For example:

.. code-block:: python

  Txn.application_args.length() # get the number of application arguments in the transaction
  Txn.application_args[0] # get the first application argument
  Txn.application_args[1] # get the second application argument

  # as of TEAL v5, PyTeal expressions can be used to dynamically index into array properties as well
  Txn.application_args[Txn.application_args.length() - Int(1)] # get the last application argument

.. _txn_special_case_arrays:

Special case: :code:`Txn.accounts` and :code:`Txn.applications`
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

The :code:`Txn.accounts` and :code:`Txn.applications` arrays are special cases. Normal arrays in
PyTeal are :code:`0`-indexed, but these are :code:`1`-indexed with special values at index :code:`0`.

For the accounts array, :code:`Txn.accounts[0]` is always equivalent to :code:`Txn.sender()`.

For the applications array, :code:`Txn.applications[0]` is always equivalent to :code:`Txn.application_id()`.

**IMPORTANT:** Since these arrays are :code:`1`-indexed, their lengths are handled differently.
For example, if :code:`Txn.accounts.length()` or :code:`Txn.applications.length()` is 2, then
indexes :code:`0`, :code:`1`, and :code:`2` will be present. In fact, the index :code:`0` will
always evaluate to the special values above, even when :code:`length()` is :code:`0`.

Atomic Transfer Groups
----------------------

`Atomic Transfers <https://developer.algorand.org/docs/features/atomic_transfers/>`_ are irreducible
batch transactions that allow groups of transactions to be submitted at one time. If any of the
transactions fail, then all the transactions will fail. PyTeal allows programs to access information
about the transactions in an atomic transfer group using the :any:`Gtxn` object. This object acts
like a list of :any:`TxnObject`, meaning all of the above transaction fields on :code:`Txn` are
available on the elements of :code:`Gtxn`. For example:

.. code-block:: python

  Gtxn[0].sender() # get the sender of the first transaction in the atomic transfer group
  Gtxn[1].receiver() # get the receiver of the second transaction in the atomic transfer group

  # as of TEAL v3, PyTeal expressions can be used to dynamically index into Gtxn as well
  Gtxn[Txn.group_index() - Int(1)].sender() # get the sender of the previous transaction in the atomic transfer group

:code:`Gtxn` is zero-indexed and the maximum size of an atomic transfer group is 16. The size of the
current transaction group is available as :any:`Global.group_size()`. A standalone transaction will
have a group size of :code:`1`.

To find the current transaction's index in the transfer group, use :any:`Txn.group_index() <TxnObject.group_index>`. If the
current transaction is standalone, it's group index will be :code:`0`.

Inner Transactions
------------------

.. note::
    Inner transactions are only available in TEAL version 5 or higher.

Inner transactions can be created and submitted with expressions from the :any:`InnerTxnBuilder` class.
The properties of the most recently submitted inner transaction can be accessed using the :any:`InnerTxn`
object. This object is an instance of :any:`TxnObject`, meaning all of the above transaction fields
on :code:`Txn` are available on :code:`InnerTxn` as well.

Global Parameters
-----------------

Information about the current state of the blockchain can be obtained using the following
:any:`Global` expressions:

=========================================== ======================= ================ =============================================================
Operator                                    Type                    Min TEAL Version Notes
=========================================== ======================= ================ =============================================================
:any:`Global.min_txn_fee()`                 :code:`TealType.uint64` 2                in microAlgos  
:any:`Global.min_balance()`                 :code:`TealType.uint64` 2                in mircoAlgos
:any:`Global.max_txn_life()`                :code:`TealType.uint64` 2                number of rounds
:any:`Global.zero_address()`                :code:`TealType.bytes`  2                32 byte address of all zero bytes
:any:`Global.group_size()`                  :code:`TealType.uint64` 2                number of txns in this atomic transaction group, at least 1
:any:`Global.logic_sig_version()`           :code:`TealType.uint64` 2                the maximum supported TEAL version
:any:`Global.round()`                       :code:`TealType.uint64` 2                the current round number
:any:`Global.latest_timestamp()`            :code:`TealType.uint64` 2                the latest confirmed block UNIX timestamp
:any:`Global.current_application_id()`      :code:`TealType.uint64` 2                the ID of the current application executing
:any:`Global.creator_address()`             :code:`TealType.bytes`  3                32 byte address of the creator of the current application
:any:`Global.current_application_address()` :code:`TealType.bytes`  5                32 byte address of the current application controlled account
:any:`Global.group_id()`                    :code:`TealType.bytes`  5                32 byte ID of the current transaction group
=========================================== ======================= ================ =============================================================
