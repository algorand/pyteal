.. _abi:

ABI Support
===========

TODO: brief description

TODO: top-level warning about experimental nature of some APIs
TODO: warning about how ABI types are intended to be used at the moment (for standard serialization at the incoming and outgoing layers of contract) - internal use may be extremely inefficient with ABI types
TODO: warning about how internal representation of ABI types may change over time

Types
------

The ABI supports a variety of types whose encodings are standardized.

Before we introduce these ABI types, it's important to understand the fundamentals of how PyTeal's ABI type system works.

:any:`abi.BaseType` is an abstract base class that all ABI type classes inherit from. This class defines a few methods common to all ABI types:

* :any:`abi.BaseType.decode()` is used to decode and populate a type's value from an encoded byte string.
* :any:`abi.BaseType.encode()` is used to encode a type's value into an encoded byte string.
* :any:`abi.BaseType.type_spec()` is used to get an instance of :any:`abi.TypeSpec` that describes that type.

:any:`abi.TypeSpec` is an abstract base class used to describe types. TODO: finish description

ABI types are divided into a few categories, each explained in the following sections.

Basic Types
~~~~~~~~~~~

TODO: brief intro

Definitions
^^^^^^^^^^^^^^^^^^^^^^^^

PyTeal supports the following basic static types:

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

\*A note about :any:`abi.Tuple`: a proper implementation of this type requires a variable amount of generic arguments. Python 3.11 will support this with the introduction of `PEP 646 - Variadic Generics <https://peps.python.org/pep-0646/>`_, but until then it will not be possible to make :code:`abi.Tuple` a generic type. As a workaround, we have introduced the following subclasses of :code:`abi.Tuple` for fixed amounts of generic arguments:

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

Static vs Dynamic Types
^^^^^^^^^^^^^^^^^^^^^^^^

An important property of the above types are whether they are static or dynamic.

Static types are defined as types whose encoded length does not depend on the value of that type. This property allows encoding and decoding of static types to be more efficient.

Likewise, dynamic types are defined as types whose encoded length does in fact depend on the value that type has. Due to this dependency, the code that PyTeal generates to encode, decode, and manipulate dynamic types is more complex and less efficient than the code needed for static types.

Because of the difference in complexity and efficiency when working with static and dynamic types, we strongly recommend using static types over dynamic types whenever possible.

Usage
^^^^^^^^^^^^^^^^^^^^^^^^

TODO: explain usage and show examples

Limitations
^^^^^^^^^^^^^^^^^^^^^^^^

TODO: warn about code inefficiencies and type size limitations

Reference Types
~~~~~~~~~~~~~~~~~

In addition to the basic types defined above, 

Definitions
^^^^^^^^^^^^^^^^^^^^^^^^

PyTeal supports the following reference types:

====================== ====================== ================ =======================================================================================================================================================
PyTeal Type            ARC-4 Type             Dynamic / Static Description
====================== ====================== ================ =======================================================================================================================================================
:any:`abi.Account`     :code:`account`        Static           Represents an additional account that the current transaction can access, stored in the :any:`Txn.accounts <TxnObject.accounts>` array
:any:`abi.Asset`       :code:`asset`          Static           Represents an additional asset that the current transaction can access, stored in the :any:`Txn.assets <TxnObject.assets>` array
:any:`abi.Application` :code:`application`    Static           Represents an additional application that the current transaction can access, stored in the :any:`Txn.applications <TxnObject.applications>` array
====================== ====================== ================ =======================================================================================================================================================

Usage
^^^^^^^^^^^^^^^^^^^^^^^^

TODO: explain usage and show examples

Limitations
^^^^^^^^^^^^^^^^^^^^^^^^

TODO: explain limitations, such as can't be created directly, or used as method return value

Transaction Types
~~~~~~~~~~~~~~~~~

TODO: brief description

Definitions
^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^

TODO: explain usage and show examples

Limitations
^^^^^^^^^^^^^^^^^^^^^^^^

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

TODO: warning again about experimental design
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
TODO: warning again about experimental design

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
