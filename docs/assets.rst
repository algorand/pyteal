.. _assets:

Asset Information
=================

In addition to :ref:`manipulating state on the blockchain <state>`, stateful
smart contracts can also look up information about assets and account balances.

Algo Balances
-------------

The :any:`Balance` expression can be used to look up an account's balance in microAlgos (1 Algo = 1,000,000 microAlgos).
For example,

.. code-block:: python

    senderBalance = Balance(Txn.sender()) # get the balance of the sender
    account1Balance = Balance(Txn.accounts[1]) # get the balance of Txn.accounts[1]

The :any:`MinBalance` expression can be used to find an account's `minimum balance <https://developer.algorand.org/docs/features/accounts/#minimum-balance>`_.
This amount is also in microAlgos. For example,

.. code-block:: python

    senderMinBalance = MinBalance(Txn.sender()) # get the minimum balance of the sender by passing the account address (bytes)
    account1MinBalance = MinBalance(Txn.accounts[1]) # get the minimum balance of Txn.accounts[1] by passing the account address (bytes)

Additionally, :any:`Balance` and :any:`MinBalance` can be used together to calculate how many Algos
an account can spend without closing. For example,

.. code-block:: python

    senderSpendableBalance = Balance(Txn.sender()) - MinBalance(Txn.sender()) # calculate how many Algos the sender can spend
    account1SpendableBalance = Balance(Txn.accounts[1]) - MinBalance(Txn.accounts[1]) # calculate how many Algos Txn.accounts[1] can spend

Asset Holdings
--------------

In addition to Algos, the Algorand blockchain also supports additional on-chain assets called `Algorand Standard Assets (ASAs) <https://developer.algorand.org/docs/features/asa/>`_.
The :any:`AssetHolding` group of expressions can be used to look up information about the ASAs that
an account holds.

Similar to :ref:`external state expressions <external_state>`, these expression return a :any:`MaybeValue`.
This value cannot be used directly, but has methods :any:`MaybeValue.hasValue()` and :any:`MaybeValue.value()`.

If the account has opted into the asset being looked up, :code:`hasValue()` will return :code:`1`
and :code:`value()` will return the value being looked up (either the asset's balance or frozen status).
Otherwise, :code:`hasValue()` and :code:`value()` will return :code:`0`.

Balances
~~~~~~~~

The :any:`AssetHolding.balance` expression can be used to look up how many units of an asset an
account holds. For example,

.. code-block:: python

    # get the balance of the sender for asset `Txn.assets[0]`
    # if the account is not opted into that asset, returns 0
    senderAssetBalance = AssetHolding.balance(Txn.sender(), Txn.assets[0])
    program = Seq([
        senderAssetBalance,
        senderAssetBalance.value()
    ])

    # get the balance of Txn.accounts[1] for asset `Txn.assets[1]`
    # if the account is not opted into that asset, exit with an error
    account1AssetBalance = AssetHolding.balance(Txn.accounts[1], Txn.assets[1])
    program = Seq([
        account1AssetBalance,
        Assert(account1AssetBalance.hasValue()),
        account1AssetBalance.value()
    ])

Frozen
~~~~~~

The :any:`AssetHolding.frozen` expression can be used to check if an asset is frozen for an account.
A value of :code:`1` indicates frozen and :code:`0` indicates not frozen. For example,

.. code-block:: python

    # get the frozen status of the sender for asset `Txn.assets[0]`
    # if the account is not opted into that asset, returns 0
    senderAssetFrozen = AssetHolding.frozen(Txn.sender(), Txn.assets[0])
    program = Seq([
        senderAssetFrozen,
        senderAssetFrozen.value()
    ])

    # get the frozen status of Txn.accounts[1] for asset `Txn.assets[1]`
    # if the account is not opted into that asset, exit with an error
    account1AssetFrozen = AssetHolding.frozen(Txn.accounts[1], Txn.assets[1])
    program = Seq([
        account1AssetFrozen,
        Assert(account1AssetFrozen.hasValue()),
        account1AssetFrozen.value()
    ])

Asset Parameters
----------------

Every ASA has parameters that contain information about the asset and how it behaves. These
parameters can be read by TEAL applications for any asset in the :any:`Txn.assets <TxnObject.assets>`
array.

The :any:`AssetParam` group of expressions are used to access asset parameters. Like :code:`AssetHolding`,
these expressions return a :any:`MaybeValue`.

The :code:`hasValue()` method will return :code:`0` only if the asset being looked up does not exist
(i.e. the ID in :code:`Txn.assets` does not represent an asset).

For optional parameters that are not set, :code:`hasValue()` will still return :code:`1` and :code:`value()`
will return a zero-length byte string (all optional parameters are :code:`TealType.bytes`).

The different parameters that can be accessed are summarized by the table below. More information
about each parameter can be found on the `Algorand developer website <https://developer.algorand.org/docs/features/asa/#asset-parameters>`_.

================================= ======================= ==========================================================
Expression                        Type                    Description
================================= ======================= ==========================================================
:any:`AssetParam.total()`         :code:`TealType.uint64` The total number of units of the asset.
:any:`AssetParam.decimals()`      :code:`TealType.uint64` The number of decimals the asset should be formatted with.
:any:`AssetParam.defaultFrozen()` :code:`TealType.uint64` Whether the asset is frozen by default.
:any:`AssetParam.unitName()`      :code:`TealType.bytes`  The name of the asset's units.
:any:`AssetParam.name()`          :code:`TealType.bytes`  The name of the asset.
:any:`AssetParam.url()`           :code:`TealType.bytes`  A URL associated with the asset.
:any:`AssetParam.metadataHash()`  :code:`TealType.bytes`  A 32-byte hash associated with the asset.
:any:`AssetParam.manager()`       :code:`TealType.bytes`  The address of the asset's manager account.
:any:`AssetParam.reserve()`       :code:`TealType.bytes`  The address of the asset's reserve account.
:any:`AssetParam.freeze()`        :code:`TealType.bytes`  The address of the asset's freeze account.
:any:`AssetParam.clawback()`      :code:`TealType.bytes`  The address of the asset's clawback account.
================================= ======================= ==========================================================

Here's an example that uses an asset parameter:

.. code-block:: python

    # get the total number of units for asset `Txn.assets[0]`
    # if the asset is invalid, exit with an error
    assetTotal = AssetParam.total(Txn.assets[0])

    program = Seq([
        assetTotal,
        Assert(assetTotal.hasValue()),
        assetTotal.value()
    ])
