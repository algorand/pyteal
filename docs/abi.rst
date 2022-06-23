.. _abi:

ABI Support
===========

TODO: brief description

.. warning::
  ABI support is still taking shape and is subject to backwards incompatible changes.
    * Based on feedback, the API and usage patterns are likely to change.
    * For the following use cases, feel encouraged to rely on abstractions.  Expect a best-effort attempt to minimize backwards incompatible changes along with a migration path.

       * :any:`ABIReturnSubroutine` usage for ABI Application entry point definition.

       * :any:`Router` usage for defining how to route program invocations.
    * For general purpose :any:`Subroutine` definition usage, use at your own risk.  Based on feedback, the API and usage patterns will change more freely and with less effort to provide migration paths.

TODO: warning about how ABI types are intended to be used at the moment (for standard serialization at the incoming and outgoing layers of contract) - internal use may be extremely inefficient with ABI types
TODO: warning about how internal representation of ABI types may change over time

Types
------

The ABI supports a variety of types whose encodings are standardized.

Fundamentals
~~~~~~~~~~~~

Before we introduce these ABI types, it's important to understand the fundamentals of how PyTeal's ABI type system works.

:code:`abi.BaseType`
^^^^^^^^^^^^^^^^^^^^

:any:`abi.BaseType` is an abstract base class that all ABI type classes inherit from. This class defines a few methods common to all ABI types:

* :any:`abi.BaseType.decode()` is used to decode and populate a type's value from an encoded byte string.
* :any:`abi.BaseType.encode()` is used to encode a type's value into an encoded byte string.
* :any:`abi.BaseType.type_spec()` is used to get an instance of :any:`abi.TypeSpec` that describes that type.

:code:`abi.TypeSpec`
^^^^^^^^^^^^^^^^^^^^

:any:`abi.TypeSpec` is an abstract base class used to describe ABI types. Every child class of :code:`abi.BaseType` also has a companion :code:`abi.TypeSpec` child class. The :code:`abi.TypeSpec` class has a few methods that return information about the type it represents, but one of the class's most important features is the method :any:`abi.TypeSpec.new_instance()`, which creates and returns a new :any:`abi.BaseType` instance of the ABI type it represents.

Static vs Dynamic Types
^^^^^^^^^^^^^^^^^^^^^^^

An important property of an ABI type is whether it is static or dynamic.

Static types are defined as types whose encoded length does not depend on the value of that type. This property allows encoding and decoding of static types to be more efficient.

Likewise, dynamic types are defined as types whose encoded length does in fact depend on the value that type has. Due to this dependency, the code that PyTeal generates to encode, decode, and manipulate dynamic types is more complex and generally less efficient than the code needed for static types.

Because of the difference in complexity and efficiency when working with static and dynamic types, **we strongly recommend using static types over dynamic types whenever possible**.

Instantiating Types
^^^^^^^^^^^^^^^^^^^

There are a few ways to create an instance of an ABI type. Each method produces the same result, but some may be more convenient than others.

With the Constructor
""""""""""""""""""""""

The most obvious way is to use its constructor, like so:

.. code-block:: python

    myUint8 = abi.Uint8()
    myUint64 = abi.Uint64()
    myArrayOf12Uint8s = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint8TypeSpec(), 12))

For simple types, using the constructor is straightforward and works as you would expect. However, more complex types like :any:`abi.StaticArray` have type-level arguments, so their constructor must take an :any:`abi.TypeSpec` which fully defines all necessary arguments. These types can be created with a constructor, but it's often not the most convenient way to do so.

With an :code:`abi.TypeSpec` Instance
""""""""""""""""""""""""""""""""""""""

You may remember that :code:`abi.TypeSpec` has a :any:`new_instance() <abi.TypeSpec.new_instance>` method that can be used to instantiate ABI types. This is another way of instantiating ABI types, if you happen to have an :code:`abi.TypeSpec` instance available. For example:

.. code-block:: python

    myUintType = abi.Uint8TypeSpec()
    myUint8 = myUintType.new_instance()

    myArrayType = abi.StaticArrayTypeSpec(myUintType, 12)
    myArrayOf12Uint8s = myArrayType.new_instance()

With :code:`abi.make`
"""""""""""""""""""""

Using :code:`abi.TypeSpec.new_instance()` makes sense if you already have an instance of the right :code:`abi.TypeSpec`, but otherwise it's not much better than using the constructor. Because of this, we have the :any:`abi.make` method, which is perhaps the most convenient way to create a complex type.

To use it, you pass in a Python type annotation that describes the ABI type, and :code:`abi.make` will create an instance of it for you. For example:

.. code-block:: python

    from typing import Literal

    myUint8 = abi.make(abi.Uint8)
    myUint64 = abi.make(abi.Uint64)
    myArrayOf12Uint8s = abi.make(abi.StaticArray[abi.Uint8, Literal[12]])

.. note::
    Since Python does not allow integers to be directly embedded in type annotations, you must wrap any integer arguments in the :code:`Literal` annotation from the :code:`typing` module.

Categories
~~~~~~~~~~

There are three categories of ABI types:

1. Basic types
2. Reference types
3. Transaction types

Each of which is described in detail in the following subsections.

Basic Types
^^^^^^^^^^^^^^^^^^^^^^^^

Basic types are the most straightforward category of ABI types. These types are used to hold values and they have no other side effects, in contrast to the other categories of types.

Definitions
"""""""""""""""""""""

PyTeal supports the following basic types:

============================================== ====================== ================================= =======================================================================================================================================================
PyTeal Type                                    ARC-4 Type             Dynamic / Static                  Description
============================================== ====================== ================================= =======================================================================================================================================================
:any:`abi.Uint8`                               :code:`uint8`          Static                            An 8-bit unsigned integer
:any:`abi.Uint16`                              :code:`uint16`         Static                            A 16-bit unsigned integer
:any:`abi.Uint32`                              :code:`uint32`         Static                            A 32-bit unsigned integer
:any:`abi.Uint64`                              :code:`uint64`         Static                            A 64-bit unsigned integer
:any:`abi.Bool`                                :code:`bool`           Static                            A boolean value that can be either 0 or 1
:any:`abi.Byte`                                :code:`byte`           Static                            An 8-bit unsigned integer. This is an alias for :code:`abi.Uint8` that should be used to indicate non-numeric data, such as binary arrays.
:any:`abi.StaticArray[T,N] <abi.StaticArray>`  :code:`T[N]`           Static if :code:`T` is static     A fixed-length array of :code:`T` with :code:`N` elements
:any:`abi.Address`                             :code:`address`        Static                            A 32-byte Algorand address. This is an alias for :code:`abi.StaticArray[abi.Byte, Literal[32]]`.
:any:`abi.DynamicArray[T] <abi.DynamicArray>`  :code:`T[]`            Dynamic                           A variable-length array of :code:`T`
:any:`abi.String`                              :code:`string`         Dynamic                           A variable-length byte array assumed to contain UTF-8 encoded content. This is an alias for :code:`abi.DynamicArray[abi.Byte]`.
:any:`abi.Tuple`\*                             :code:`(...)`          Static if all elements are static A tuple of multiple types
============================================== ====================== ================================= =======================================================================================================================================================

.. note::
    \*A proper implementation of :any:`abi.Tuple` requires a variable amount of generic arguments. Python 3.11 will support this with the introduction of `PEP 646 - Variadic Generics <https://peps.python.org/pep-0646/>`_, but until then it will not be possible to make :code:`abi.Tuple` a generic type. As a workaround, we have introduced the following subclasses of :code:`abi.Tuple` for fixed amounts of generic arguments:

    * :any:`abi.Tuple0`: a tuple of zero values, :code:`()`
    * :any:`abi.Tuple1[T1] <abi.Tuple1>`: a tuple of one value, :code:`(T1)`
    * :any:`abi.Tuple2[T1,T2] <abi.Tuple2>`: a tuple of two values, :code:`(T1,T2)`
    * :any:`abi.Tuple3[T1,T2,T3] <abi.Tuple3>`: a tuple of three values, :code:`(T1,T2,T3)`
    * :any:`abi.Tuple4[T1,T2,T3,T4] <abi.Tuple4>`: a tuple of four values, :code:`(T1,T2,T3,T4)`
    * :any:`abi.Tuple5[T1,T2,T3,T4,T5] <abi.Tuple5>`: a tuple of five values, :code:`(T1,T2,T3,T4,T5)`

These ARC-4 types are not yet supported in PyTeal:

* Non-power-of-2 unsigned integers under 64 bits, i.e. :code:`uint24`, :code:`uint48`, :code:`uint56`
* Unsigned integers larger than 64 bits
* Fixed point unsigned integers, i.e. :code:`ufixed<N>x<M>`

Usage
"""""""""""""""""""""

Setting Values
''''''''''''''''

All basic types have a :code:`set()` method which can be used to assign a value. The arguments for this method differ depending on the ABI type. For convenience, here are links to the docs for each class's method:

* :any:`abi.Uint.set()`, which is used by all :code:`abi.Uint` classes and :code:`abi.Byte`
* :any:`abi.Bool.set()`
* :any:`abi.StaticArray.set()`
* :any:`abi.Address.set()`
* :any:`abi.DynamicArray.set()`
* :any:`abi.String.set()`
* :any:`abi.Tuple.set()`

A brief example is below. Please consult the documentation linked above for each method to learn more about specific usage and behavior.

.. code-block:: python

    myAddress = abi.make(abi.Address)
    myBool = abi.make(abi.Bool)
    myUint64 = abi.make(abi.Uint64)
    myTuple = abi.make(abi.Tuple3[abi.Address, abi.Bool, abi.Uint64])

    program = Seq(
        myAddress.set(Txn.sender()),
        myBool.set(Txn.fee() == Int(0)),
        myUint64.set(5000),
        myTuple.set(myAddress, myBool, myUint64)
    )

Getting Values
''''''''''''''''''''''

All basic types that represent a single value have a :code:`get()` method, which can be used to extract that value. The supported types and methods are:

* :any:`abi.Uint.get()`, which is used by all :code:`abi.Uint` classes and :code:`abi.Byte`
* :any:`abi.Bool.get()`
* :any:`abi.Address.get()`
* :any:`abi.String.get()`

A brief example is below. Please consult the documentation linked above for each method to learn more about specific usage and behavior.

.. code-block:: python

    myUint64 = abi.make(abi.Uint64)

    program = Seq(
        myUint64.decode(Txn.application_args[1]),
        Assert(myUint64.get() != Int(0))
    )

Getting Values at Indexes
''''''''''''''''''''''''''

The types :code:`abi.StaticArray`, :code:`abi.Address`, :code:`abi.DynamicArray`, :code:`abi.String`, and :code:`abi.Tuple` are compound types, meaning they contain other types whose values can be extracted. The :code:`__getitem__` method, accessible by using square brackets to "index into" an object, can be used to extract these values.

The supported methods are:

* :any:`abi.StaticArray.__getitem__`, used for :code:`abi.StaticArray` and :code:`abi.Address`
* :any:`abi.Array.__getitem__`, used for :code:`abi.DynamicArray` and :code:`abi.String`
* :any:`abi.Tuple.__getitem__`

Be aware that these methods return a :code:`ComputedValue`, TODO link to Computed Value section

A brief example is below. Please consult the documentation linked above for each method to learn more about specific usage and behavior.

.. code-block:: python

    myTuple = abi.make(abi.Tuple3[abi.Address, abi.Bool, abi.Uint64])
    myBool = abi.make(abi.Bool)

    program = Seq(
        myTuple.decode(Txn.application_args[1]),
        myBool.set(myTuple[2]),
        Assert(myBool.get())
    )

Limitations
"""""""""""""""""""""

TODO: warn about code inefficiencies and type size limitations

Reference Types
^^^^^^^^^^^^^^^^^^^^^^^^

TODO: brief description

Definitions
""""""""""""""""""""""""""""""""""""""""""

PyTeal supports the following reference types:

====================== ====================== ================ =======================================================================================================================================================
PyTeal Type            ARC-4 Type             Dynamic / Static Description
====================== ====================== ================ =======================================================================================================================================================
:any:`abi.Account`     :code:`account`        Static           Represents an additional account that the current transaction can access, stored in the :any:`Txn.accounts <TxnObject.accounts>` array
:any:`abi.Asset`       :code:`asset`          Static           Represents an additional asset that the current transaction can access, stored in the :any:`Txn.assets <TxnObject.assets>` array
:any:`abi.Application` :code:`application`    Static           Represents an additional application that the current transaction can access, stored in the :any:`Txn.applications <TxnObject.applications>` array
====================== ====================== ================ =======================================================================================================================================================

Usage
""""""""""""""""""""""""""""""""""""""""""

TODO: explain usage and show examples

Limitations
""""""""""""""""""""""""""""""""""""""""""

TODO: explain limitations, such as can't be created directly, or used as method return value

Transaction Types
^^^^^^^^^^^^^^^^^^^^^^^^

TODO: brief description

Definitions
""""""""""""""""""""""""""""""""""""""""""

PyTeal supports the following transaction types:

=================================== ====================== ================ =======================================================================================================================================================
PyTeal Type                         ARC-4 Type             Dynamic / Static Description
=================================== ====================== ================ =======================================================================================================================================================
:any:`abi.Transaction`              :code:`txn`            Static           A catch-all for any transaction type
:any:`abi.PaymentTransaction`       :code:`pay`            Static           A payment transaction
:any:`abi.KeyRegisterTransaction`   :code:`keyreg`         Static           A key registration transaction
:any:`abi.AssetConfigTransaction`   :code:`acfg`           Static           An asset configuration transaction
:any:`abi.AssetTransferTransaction` :code:`axfer`          Static           An asset transfer transaction
:any:`abi.AssetFreezeTransaction`   :code:`afrz`           Static           An asset freeze transaction
:any:`abi.AssetTransferTransaction` :code:`appl`           Static           An application call transaction
=================================== ====================== ================ =======================================================================================================================================================

Usage
""""""""""""""""""""""""""""""""""""""""""

TODO: explain usage and show examples

Limitations
""""""""""""""""""""""""""""""""""""""""""

TODO: explain limitations, such as can't be created directly, used as method return value, or embedded in other types

Computed Values
~~~~~~~~~~~~~~~~~

TODO: explain what ComputedValue is, where it appears, how to use it, and why it's necessary

Subroutines with ABI Types
--------------------------

TODO: brief description

ABI Arguments with the Subroutine decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: brief description

Definition
~~~~~~~~~~~~~~~~~

TODO: explain how to create a subroutine with the existing Subroutine decorator and ABI arguments

Usage
~~~~~~~~~~~~~~~~~

TODO: explain how to call a subroutine with ABI arguments

ABIReturnSubroutine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::
  :any:`ABIReturnSubroutine` is still taking shape and is subject to backwards incompatible changes.

  * For ABI Application entry point definition, feel encouraged to use :any:`ABIReturnSubroutine`.  Expect a best-effort attempt to minimize backwards incompatible changes along with a migration path.
  * For general purpose usage, use at your own risk.  Based on feedback, the API and usage patterns will change more freely and with less effort to provide migration paths.

TODO: brief overview of why this is necessary and when it should be used

Definition
~~~~~~~~~~~~~~~~~

TODO: explain how to create a subroutine using ABIReturnSubroutine with ABI return values

Usage
~~~~~~~~~~~~~~~~~

TODO: explain how to call an ABIReturnSubroutine and how to process the return value

Creating an ARC-4 Program with the ABI Router
----------------------------------------------------

TODO: brief intro

.. warning::
  :any:`Router` usage is still taking shape and is subject to backwards incompatible changes.

  Feel encouraged to use :any:`Router` and expect a best-effort attempt to minimize backwards incompatible changes along with a migration path.

Registering Bare App Calls
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: explain bare app calls and how they can be added to a Router

Registering Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: explain methods and how they can be added to a Router
TODO: warning about input type validity -- no verification is done for you (right now)

Building and Compiling a Router Program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: explain how to build/compile a Router program to get the TEAL code + contract JSON

Calling an ARC-4 Program
--------------------------

TODO: brief intro

Off-Chain, from an SDK or :code:`goal`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: leave pointers to SDK/goal documentation about how to invoke ABI calls

On-Chain, in an Inner Transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: explain how this is possible but there is no simple way to do it in PyTeal yet; once it is, we should update this section
