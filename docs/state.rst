.. _state:

State Access and Manipulation
=============================

PyTeal can be used to write `Stateful Algorand Smart Contracts <https://developer.algorand.org/docs/features/asc1/stateful/>`_
as well. Stateful contracts, also known as applications, can access and manipulate state on the
Algorand blockchain.

There are multiple types of state that an application can use.
State consists of key-value pairs, where keys are byte slices and values vary by type of state.

=================== ===================== ===============================================
Type of State       Type of Key           Type of Value
=================== ===================== ===============================================
Global State        :any:`TealType.bytes` :any:`TealType.uint64` or :any:`TealType.bytes`
Local State         :any:`TealType.bytes` :any:`TealType.uint64` or :any:`TealType.bytes`
Boxes               :any:`TealType.bytes` :any:`TealType.bytes`
=================== ===================== ===============================================

State Operation Table
---------------------

================== ======================= ======================== ======================== ===================== =======================
Context            Create                  Write                    Read                     Delete                Check If Exists
================== ======================= ======================== ======================== ===================== =======================
Current App Global                         :any:`App.globalPut`     :any:`App.globalGet`     :any:`App.globalDel`  :any:`App.globalGetEx`
Current App Local                          :any:`App.localPut`      :any:`App.localGet`      :any:`App.localDel`   :any:`App.localGetEx`
Other App Global                                                    :any:`App.globalGetEx`                         :any:`App.globalGetEx`
Other App Local                                                     :any:`App.localGetEx`                          :any:`App.localGetEx`
Current App Boxes  :any:`App.box_create`   :any:`App.box_put`       :any:`App.box_extract`   :any:`App.box_delete` :any:`App.box_length`
                   :any:`App.box_put`      :any:`App.box_replace`   :any:`App.box_get`                             :any:`App.box_get`
================== ======================= ======================== ======================== ===================== =======================

Global State
------------

Global state consists of key-value pairs that are stored in the application's global context. It can be
manipulated as follows:

Writing Global State
~~~~~~~~~~~~~~~~~~~~

To write to global state, use the :any:`App.globalPut` function. The first argument is the key to
write to, and the second argument is the value to write. For example:

.. code-block:: python

    App.globalPut(Bytes("status"), Bytes("active")) # write a byte slice
    App.globalPut(Bytes("total supply"), Int(100)) # write a uint64

Reading Global State
~~~~~~~~~~~~~~~~~~~~

To read from global state, use the :any:`App.globalGet` function. The only argument it takes is the
key to read from. For example:

.. code-block:: python

    App.globalGet(Bytes("status"))
    App.globalGet(Bytes("total supply"))

If you try to read from a key that does not exist in your app's global state, the integer `0` is
returned.

Deleting Global State
~~~~~~~~~~~~~~~~~~~~~

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
local state. This is done by passing in the address of an account. In order to read or manipulate
an account's local state, that account must be presented in the
:any:`Txn.accounts <TxnObject.accounts>` array.

**Note:** The :code:`Txn.accounts` array does not behave like a normal array. It's actually a
:code:`1`-indexed array with a special value at index :code:`0`, the sender's account.
See :ref:`txn_special_case_arrays` for more details.

Writing Local State
~~~~~~~~~~~~~~~~~~~

To write to the local state of an account, use the :any:`App.localPut` function. The first argument
is the address of the account to write to, the second argument is the key to write to, and the
third argument is the value to write. For example:

.. code-block:: python

    App.localPut(Txn.sender(), Bytes("role"), Bytes("admin")) # write a byte slice to the sender's account
    App.localPut(Txn.sender(), Bytes("balance"), Int(10)) # write a uint64 to the sender's account
    App.localPut(Txn.accounts[1], Bytes("balance"), Int(10)) # write a uint64 to Txn.account[1]

**Note:** It is only possible to write to the local state of an account if that account has opted
into your application. If the account has not opted in, the program will fail with an error. The
function :any:`App.optedIn` can be used to check if an account has opted into an app.

Reading Local State
~~~~~~~~~~~~~~~~~~~

To read from the local state of an account, use the :any:`App.localGet` function. The first argument
is the address of the account to read from, and the second argument is the key to read. For example:

.. code-block:: python

    App.localGet(Txn.sender(), Bytes("role")) # read from the sender's account
    App.localGet(Txn.sender(), Bytes("balance")) # read from the sender's account
    App.localGet(Txn.accounts[1], Bytes("balance")) # read from Txn.accounts[1]

If you try to read from a key that does not exist in the account's local state, the integer :code:`0`
is returned.

Deleting Local State
~~~~~~~~~~~~~~~~~~~~

To delete a key from local state of an account, use the :any:`App.localDel` function. The first
argument is the address of the corresponding account, and the second argument is the key to delete.
For example:

.. code-block:: python

    App.localDel(Txn.sender(), Bytes("role")) # delete "role" from the sender's account
    App.localDel(Txn.sender(), Bytes("balance")) # delete "balance" from the sender's account
    App.localDel(Txn.accounts[1], Bytes("balance")) # delete "balance" from Txn.accounts[1]

If you try to delete a key that does not exist in the account's local state, nothing happens.

.. _external_state:

External State
--------------

The above functions allow an app to read and write state in its own context. Additionally, it's
possible for applications to read state written by other applications. This is possible using the
:any:`App.globalGetEx` and :any:`App.localGetEx` functions.

Unlike the other state access functions, :any:`App.globalGetEx` and :any:`App.localGetEx` return a
:any:`MaybeValue`. This value cannot be used directly, but has methods :any:`MaybeValue.hasValue()`
and :any:`MaybeValue.value()`. If the key being accessed exists in the context of the app
being read, :code:`hasValue()` will return :code:`1` and :code:`value()` will return its value. Otherwise,
:code:`hasValue()` and :code:`value()` will return :code:`0`.

**Note:** Even though the :any:`MaybeValue` returned by :any:`App.globalGetEx` and
:any:`App.localGetEx` cannot be used directly, it **must** be included in the application before
:code:`hasValue()` and :code:`value()` are called on it. You will probably want to use :any:`Seq` to
do this.

Since these functions are the only way to check whether a key exists, it can be useful to use them
in the current application's context too.

External Global
~~~~~~~~~~~~~~~

To read a value from the global state of another application, use the :any:`App.globalGetEx`
function.

In order to use this function you need to pass in an integer that represents an application to
read from. This integer corresponds to an actual application ID that appears in the
:any:`Txn.applications <TxnObject.applications>` array.

**Note:** The :code:`Txn.applications` array does not behave like a normal array. It's actually a
:code:`1`-indexed array with a special value at index :code:`0`, the current application's ID.
See :ref:`txn_special_case_arrays` for more details.

Now that you have an integer that represents an application to read from, pass this as the first
argument to :any:`App.globalGetEx`, and pass the key to read as the second argument. For example:

.. code-block:: python

    # get "status" from the global context of Txn.applications[0] (the current app)
    # if "status" has not been set, returns "none"
    myStatus = App.globalGetEx(Txn.applications[0], Bytes("status"))

    program = Seq([
        myStatus,
        If(myStatus.hasValue(), myStatus.value(), Bytes("none"))
    ])

    # get "status" from the global context of Txn.applications[1]
    # if "status" has not been set, returns "none"
    otherStatus = App.globalGetEx(Txn.applications[1], Bytes("status"))
    program = Seq([
        otherStatus,
        If(otherStatus.hasValue(), otherStatus.value(), Bytes("none"))
    ])

    # get "total supply" from the global context of Txn.applications[1]
    # if "total supply" has not been set, returns the default value of 0
    otherSupply = App.globalGetEx(Txn.applications[1], Bytes("total supply"))
    program = Seq([
        otherSupply,
        otherSupply.value()
    ])

External Local
~~~~~~~~~~~~~~

To read a value from an account's local state for another application, use the :any:`App.localGetEx`
function.

The first argument is the address of the account to read from (in the same format as
:any:`App.localGet`), the second argument is the ID of the application to read from, and the third
argument is the key to read.

**Note:** The second argument is the actual ID of the application to read from, not an index into
:code:`Txn.applications`. This means that you can read from any application that the account has opted
into, not just applications included in :code:`Txn.applications`. The ID :code:`0` is still a special
value that refers to the ID of the current application, but you could also use :any:`Global.current_application_id()`
or :any:`Txn.application_id() <TxnObject.application_id>` to refer to the current application.

For example:

.. code-block:: python

    # get "role" from the local state of Txn.accounts[0] (the sender) for the current app
    # if "role" has not been set, returns "none"
    myAppSenderRole = App.localGetEx(Txn.accounts[0], Int(0), Bytes("role"))
    program = Seq([
        myAppSenderRole,
        If(myAppSenderRole.hasValue(), myAppSenderRole.value(), Bytes("none"))
    ])

    # get "role" from the local state of Txn.accounts[1] for the current app
    # if "role" has not been set, returns "none"
    myAppOtherAccountRole = App.localGetEx(Txn.accounts[1], Int(0), Bytes("role"))
    program = Seq([
        myAppOtherAccountRole,
        If(myAppOtherAccountRole.hasValue(), myAppOtherAccountRole.value(), Bytes("none"))
    ])

    # get "role" from the local state of Txn.accounts[0] (the sender) for the app with ID 31
    # if "role" has not been set, returns "none"
    otherAppSenderRole = App.localGetEx(Txn.accounts[0], Int(31), Bytes("role"))
    program = Seq([
        otherAppSenderRole,
        If(otherAppSenderRole.hasValue(), otherAppSenderRole.value(), Bytes("none"))
    ])

    # get "role" from the local state of Txn.accounts[1] for the app with ID 31
    # if "role" has not been set, returns "none"
    otherAppOtherAccountRole = App.localGetEx(Txn.accounts[1], Int(31), Bytes("role"))
    program = Seq([
        otherAppOtherAccountRole,
        If(otherAppOtherAccountRole.hasValue(), otherAppOtherAccountRole.value(), Bytes("none"))
    ])

Box Storage
-----------

Box storage consists of key-value pairs that are stored in an application's local context.

The app account's minimum balance requirement (MBR) is increased with each additional box, and each additional byte in the box's name and allocated size.

.. warning::

   If one deletes an application with outstanding boxes, the MBR is not recoverable from the deleted app account.
   It is recommended that *before* app deletion, all box storage be deleted, and funds previously allocated to the MBR be withdrawn.

Box sizes and names cannot be changed after initial allocation, but they can be deleted and re-allocated.
Boxes are only visible to the application itself; in other words, an application cannot read from or write to another application's boxes on-chain.

The following sections explain how to work with boxes.

.. _Creating Boxes:

Creating Boxes
~~~~~~~~~~~~~~

To create a box, use :any:`App.box_create`, or :any:`App.box_put` method.

For :any:`App.box_create`, the first argument is the box name, and the second argument is the byte size to be allocated.

:any:`App.box_create` creates a new box with the specified name and byte length. New boxes will contain a byte string of all zeros. Performing this operation on a box that already exists will not change its contents.

If successful, :any:`App.box_create` will return :code:`0` if the box already existed, otherwise it will return :code:`1`. A failure will occur if you attempt to create a box that already exists with a different size.

For example:

.. code-block:: python

    # Allocate a box called "BoxA" of byte size 100 and ignore the return value
    Pop(App.box_create(Bytes("BoxA"), Int(100)))

    # Allocate a box called "BoxB" of byte size 90, asserting that it didn't exist before.
    Assert(App.box_create(Bytes("BoxB"), Int(90))

For :any:`App.box_put`, the first argument is the box name to create or to write to, and the second argument is the bytes to write.

.. note::

   If the box exists, then :any:`App.box_put` will write the contents to the box
   (fails when the content length is **not identical** to the existing box's byte size);
   otherwise, it will create a box containing exactly the same input bytes.

.. code-block:: python

    # create a 42 bytes length box called `poemLine` with content
    App.box_put(Bytes("poemLine"), Bytes("Of that colossal wreck, boundless and bare"))

    # write to box `poemLine` with new value
    App.box_put(Bytes("poemLine"), Bytes("The lone and level sands stretch far away."))

Writing to a Box
~~~~~~~~~~~~~~~~

To write to a box, use :any:`App.box_replace`, or :any:`App.box_put` method.

:any:`App.box_replace` writes bytes of certain length from a start index in a box.
The first argument is the box name to write into, the second argument is the starting index to write,
and the third argument is the replacement bytes. For example:

.. code-block:: python

   # replace 2 bytes starting from the 0'th byte  by `Ne` in the box named `wordleBox`
   App.box_replace(Bytes("wordleBox"), Int(0), Bytes("Ne"))

:any:`App.box_put` writes the full contents to a pre-existing box, as is mentioned in `Creating Boxes`_.

.. _Reading from a Box:

Reading from a Box
~~~~~~~~~~~~~~~~~~

To read from a box, use :any:`App.box_extract`, or :any:`App.box_get` method.

:any:`App.box_extract` reads bytes of a certain length from a start index in a Box.
The first argument is the box name to read from, the second argument is the starting index to read,
and the third argument is the length of bytes to extract. For example:

.. code-block:: python

   # extract a segment of length 10 starting at the 5th byte in a box named `NoteBook`
   App.box_extract(Bytes("NoteBook"), Int(5), Int(10))

:any:`App.box_get` gets the full contents of a box.
The only argument is the box name, and it returns a :any:`MaybeValue` containing:

- a boolean value indicating if the box exists
- the full contents of the box.

For example:

.. code-block:: python

   # get the full contents from a box named `NoteBook`, asserting that it exists
   Seq(
       contents := App.box_get(Bytes("NoteBook")),
       Assert(contents.hasValue()),
       contents.value()
   )

Deleting a Box
~~~~~~~~~~~~~~

To delete a box, use :any:`App.box_delete` method. The only argument is the box name.

:any:`App.box_delete` will return :code:`1` if the box already existed, otherwise it will return :code:`0`. Deleting a nonexistent box is allowed, but has no effect.

For example:

.. code-block:: python

    # delete the box `boxToRemove`, asserting that it existed prior to this
    Assert(App.box_delete(Bytes("boxToRemove")))

    # delete the box `mightExist` and ignore the return value
    Pop(App.box_delete(Bytes("mightExist")))

Checking if a Box Exists and Reads its Length
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check the existence of a box, use the :any:`App.box_length` method.
The only argument is the box name, and it returns a :any:`MaybeValue` containing:

- a boolean value indicating if the box exists
- the actual byte size of the box.

For example:

.. code-block:: python

   # get the length of the box `someBox`, and assert that the box exists
   Seq(
       length := App.box_length(Bytes("someBox")),
       Assert(length.hasValue()),
       length.value()
   )

.. note::

   :any:`App.box_get` can also check the existence of a box as mentioned in `Reading from a Box`_.
