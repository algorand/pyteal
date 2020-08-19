.. _state:

State Access and Manipulation
=============================

PyTeal can be used to write `Stateful Algorand Smart Contracts <https://developer.algorand.org/docs/features/asc1/stateful/>`_
as well. Stateful contracts, also known as applications, can access and manipulate state on the
Algorand blockchain.

State consists of key-value pairs, where keys are byte slices and values can be integers or byte
slices. There are multiple types of state that an application can use.

State Operation Table
---------------------

================== ==================== ====================== ==================== ======================
Context              Write                Read                 Delete               Check If Exists
================== ==================== ====================== ==================== ======================
Current App Global :any:`App.globalPut` :any:`App.globalGet`   :any:`App.globalDel` :any:`App.globalGetEx`
Current App Local  :any:`App.localPut`  :any:`App.localGet`    :any:`App.localDel`  :any:`App.localGetEx`
Other App Global                        :any:`App.globalGetEx`                      :any:`App.globalGetEx`
Other App Local                         :any:`App.localGetEx`                       :any:`App.localGetEx`
================== ==================== ====================== ==================== ======================

Global State
------------

Global state consists of key-value pairs that are stored in the application's global context. It can be
manipulated as follows:

Writing
~~~~~~~

To write to global state, use the :any:`App.globalPut` function. The first argument is the key to
write to, and the second argument is the value to write. For example:

.. code-block:: python

    App.globalPut(Bytes("status"), Bytes("active")) # write a byte slice
    App.globalPut(Bytes("total supply"), Int(100)) # write a uint64

Reading
~~~~~~~

To read from global state, use the :any:`App.globalGet` function. The only argument it takes it the
key to read from. For example:

.. code-block:: python

    App.globalGet(Bytes("status"))
    App.globalGet(Bytes("total supply"))

If you try to read from a key that does not exist in your app's global state, the integer `0` is
returned.

Deleting
~~~~~~~~

To delete a key from global state, use the :any:`App.globalDel` function. The only argument it takes
is the key to delete. For example:

.. code-block:: python

    App.globalDel(Bytes("status"))
    App.globalDel(Bytes("total supply"))

If you try to delete a key that does not exist in your app's global state, nothing happens.

Local State
-----------

Local state consists of key-value pairs that are stored in a unique context for each account that
has opted into your application. As a result, you will need to specify an account when manipulating
local state. This is done by passing in an integer that corresponds to an account. The integer `0`
is a special case that refers to the sender of the application call transaction. The integer `1`
refers to the first element in :any:`Txn.accounts <TxnObject.accounts>`, `2` refers to the second element, and so on.

Writing
~~~~~~~

To write to the local state of an account, use the :any:`App.localPut` function. The first argument
is an integers corresponding to the account to write to, the second argument is the key to write to,
and the third argument is the value to write. For example:

.. code-block:: python

    App.localPut(Int(0), Bytes("role"), Bytes("admin")) # write a byte slice to the sender's account
    App.localPut(Int(0), Bytes("balance"), Int(10)) # write a uint64 to the sender's account
    App.localPut(Int(1), Bytes("balance"), Int(10)) # write a uint64 to Txn.accounts[0]

**Note:** It is only possible to write to the local state of an account if that account has opted
into your application. If the account has not opted in, the program will fail with an error. The
function :any:`App.optedIn` can be used to check if an account has opted into an app.

Reading
~~~~~~~

To read from the local state of an account, use the :any:`App.localGet` function. The first argument
is an integer corresponding to the account to read from and the second argument is the key to read.
For example:

.. code-block:: python

    App.localGet(Int(0), Bytes("role")) # read from the sender's account
    App.localGet(Int(0), Bytes("balance")) # read from the the sender's account
    App.localGet(Int(1), Bytes("balance")) # read from Txn.accounts[0]

If you try to read from a key that does not exist in your app's global state, the integer `0` is
returned.

Deleting
~~~~~~~~

To delete a key from local state of an account, use the :any:`App.localDel` function. The first
argument is an integer corresponding to the account and the second argument is the key to delete.
For example:

.. code-block:: python

    App.localDel(Int(0), Bytes("role")) # delete "role" from the sender's account
    App.localDel(Int(0), Bytes("balance")) # delete "balance" from the the sender's account
    App.localDel(Int(1), Bytes("balance")) # delete "balance" from Txn.accounts[0]

If you try to delete a key that does not exist in the account's local state, nothing happens.

External State
--------------

The above functions allow an app to read and write state in its own context. Additionally, it's
possible for applications to read state written by other applications. This is possible using the
:any:`App.globalGetEx` and :any:`App.localGetEx` functions.

Similar to local state access, to use these functions you need to pass in an integer that represents
which application to read from. The integer `0` is a special case that refers to the current
application. The integer `1` refers to the first element in `Txn.ForeignApps <https://developer.algorand.org/docs/reference/transactions/#application-call-transaction>`_,
`2` refers to the second element, and so on. Note that the transaction field `ForeignApps` is not
accessible from TEAL at this time.

Unlike the other state access functions, :any:`App.globalGetEx` and :any:`App.localGetEx` return a
:any:`MaybeValue`. This value cannot be used directly, but has methods :any:`MaybeValue.hasValue()`
and :any:`MaybeValue.value()`. If the key being accessed exists in the global context of the app
being read, :code:`hasValue()` will return `1` and :code:`value()` will return its value. Otherwise,
:code:`hasValue()` and :code:`value()` will return `0`.

**Note:** Even though the :any:`MaybeValue` returned by :any:`App.globalGetEx` and
:any:`App.localGetEx` cannot be used directly, it **must** be included in the application before
:code:`hasValue()` and :code:`value()` are called on it. You will probably want to use :any:`Seq` to
do this.

Since these functions are the only way to check whether a key exists, it can be useful to use them
in the current application's context too.

External Global
~~~~~~~~~~~~~~~

To read a value from the global state of another application, use the :any:`App.globalGetEx`
function. The first argument is an integer corresponding to the application to read from and the
second argument is the key to read. For example:

.. code-block:: python

    # get "status" from the current global context
    # if "status" has not been set, returns "none"
    myStatus = App.globalGetEx(Int(0), Bytes("status"))
    Seq([
        myStatus,
        If(myStatus.hasValue(), myStatus.value(), Bytes("none"))
    ])

    # get "status" from the global context of Txn.ForeignApps[0]
    # if "status" has not been set, returns "none"
    otherStatus = App.globalGetEx(Int(1), Bytes("status"))
    Seq([
        otherStatus,
        If(otherStatus.hasValue(), otherStatus.value(), Bytes("none"))
    ])

    # get "total supply" from the global context of Txn.ForeignApps[0]
    # if "total supply" has not been set, returns the default value of 0
    otherSupply = App.globalGetEx(Int(1), Bytes("status"))
    Seq([
        otherSupply,
        otherSupply.value()
    ])

External Local
~~~~~~~~~~~~~~

To read a value from an account's local state for another application, use the :any:`App.localGetEx`
function. The first argument is an integer corresponding to the account to read from (in the same
format as :any:`App.localGet`), the second argument is an integer corresponding to the application
to read from, and the third argument is the key to read. For example:

.. code-block:: python

    # get "role" from the sender's local state for the current account
    # if "role" has not been set, returns "none"
    myAppSenderRole = App.localGetEx(Int(0), Int(0), Bytes("role"))
    Seq([
        myAppSenderRole,
        If(myAppSenderRole.hasValue(), myAppSenderRole.value(), Bytes("none"))
    ])

    # get "role" from the local state of Txn.accounts[0] for the current account
    # if "role" has not been set, returns "none"
    myAppOtherAccountRole = App.localGetEx(Int(1), Int(0), Bytes("role"))
    Seq([
        myAppOtherAccountRole,
        If(myAppOtherAccountRole.hasValue(), myAppOtherAccountRole.value(), Bytes("none"))
    ])

    # get "role" from the sender's local state for Txn.ForeignApps[0]
    # if "role" has not been set, returns "none"
    otherAppSenderRole = App.localGetEx(Int(0), Int(1), Bytes("role"))
    Seq([
        otherAppSenderRole,
        If(otherAppSenderRole.hasValue(), otherAppSenderRole.value(), Bytes("none"))
    ])

    # get "role" from the local state of Txn.accounts[0] for Txn.ForeignApps[0]
    # if "role" has not been set, returns "none"
    otherAppOtherAccountRole = App.localGetEx(Int(1), Int(1), Bytes("role"))
    Seq([
        otherAppOtherAccountRole,
        If(otherAppOtherAccountRole.hasValue(), otherAppOtherAccountRole.value(), Bytes("none"))
    ])
