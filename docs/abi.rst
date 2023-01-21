.. _abi:

ABI Support
===========

.. warning::
    ABI support is still taking shape and is subject to backwards incompatible changes.
        * Based on feedback, the API and usage patterns are likely to change.
        * For the following use cases, feel encouraged to rely on abstractions. Expect a best-effort attempt to minimize backwards incompatible changes along with a migration path.

            * :any:`ABIReturnSubroutine` usage for ABI Application entry point definition.

            * :any:`Router` usage for defining how to route program invocations.
        * For general purpose :any:`Subroutine` definition usage, use at your own risk. Based on feedback, the API and usage patterns will change more freely and with less effort to provide migration paths.

    For these reasons, we strongly recommend using :any:`pragma` or the :any:`Pragma` expression to pin the version of PyTeal in your source code. See :ref:`version pragmas` for more information.

`ARC-4 <https://arc.algorand.foundation/ARCs/arc-0004>`_ introduces a set of standards that increase the interoperability of smart contracts in the Algorand ecosystem. This set of standards is commonly referred to as Algorand's application binary interface, or ABI.

This page will introduce and explain the relevant concepts necessary to build a PyTeal application that adheres to the ARC-4 ABI standards.

Types
------

The ABI supports a variety of data types whose encodings are standardized.

.. note::
    Be aware that the ABI type system in PyTeal has been designed specifically for the limited use case of describing a program's inputs and outputs. At the time of writing, we **do not recommend** using ABI types in a program's internal storage or computation logic, as the more basic :any:`TealType.uint64` and :any:`TealType.bytes` :any:`Expr` types are far more efficient for these purposes.

Fundamentals
~~~~~~~~~~~~

Before diving into the specific ABI types, let us first explain the the fundamentals of PyTeal's ABI type system, which includes behavior common to all ABI types.

:code:`abi.BaseType`
^^^^^^^^^^^^^^^^^^^^

:any:`abi.BaseType` is an abstract base class that all ABI type classes inherit from. This class defines a few methods common to all ABI types:

* :any:`abi.BaseType.decode(...) <abi.BaseType.decode>` is used to decode and populate a type's value from an encoded byte string.
* :any:`abi.BaseType.encode()` is used to encode a type's value into an encoded byte string.
* :any:`abi.BaseType.type_spec()` is used to get an instance of :any:`abi.TypeSpec` that describes that type.

:code:`abi.TypeSpec`
^^^^^^^^^^^^^^^^^^^^

:any:`abi.TypeSpec` is an abstract base class used to describe ABI types. Every child class of :code:`abi.BaseType` also has a companion :code:`abi.TypeSpec` child class. The :code:`abi.TypeSpec` class has a few methods that return information about the type it represents, but one of the class's most important features is the method :any:`abi.TypeSpec.new_instance()`, which creates and returns a new :any:`abi.BaseType` instance of the ABI type it represents.

Static vs Dynamic Types
^^^^^^^^^^^^^^^^^^^^^^^

An important property of an ABI type is whether it is static or dynamic.

Static types are defined as types whose encoded length does not depend on the value of that type. This property allows encoding and decoding of static types to be more efficient. For example, the encoding of a :code:`boolean` type will always have a fixed length, regardless of whether the value is true or false.

Likewise, dynamic types are defined as types whose encoded length does in fact depend on the value that type has. For example, it's not possible to know the encoding size of a variable-sized :code:`string` type without also knowing its value. Due to this dependency on values, the code that PyTeal generates to encode, decode, and manipulate dynamic types is more complex and generally less efficient than the code needed for static types.

Because of the difference in complexity and efficiency when working with static and dynamic types, **we strongly recommend using static types over dynamic types whenever possible**. Using static types generally makes your program's resource usage more predictable as well, so you can be more confident your app has enough computation budget and storage space when using static types.

Instantiating Types
^^^^^^^^^^^^^^^^^^^

There are a few ways to create an instance of an ABI type. Each method produces the same result, but some may be more convenient than others in certain situations.

.. note::
    The following examples reference specific ABI types, which will be introduced in the :ref:`Type Categories` section.

With the Constructor
""""""""""""""""""""""

The most straightforward way is to use its constructor, like so:

.. code-block:: python

    from pyteal import *

    my_uint8 = abi.Uint8()
    my_uint64 = abi.Uint64()
    my_array = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint8TypeSpec(), 12))

For simple types, using the constructor is straightforward and works as you would expect. However, compound types like :any:`abi.StaticArray` have type-level arguments, so their constructor must take an :any:`abi.TypeSpec` which fully defines all necessary arguments. These types can be created with a constructor, but it's often not the most convenient way to do so.

With an :code:`abi.TypeSpec` Instance
""""""""""""""""""""""""""""""""""""""

Recall that :any:`abi.TypeSpec` has a :any:`new_instance() <abi.TypeSpec.new_instance>` method which instantiates ABI types. This is another way of instantiating ABI types, if you have an :any:`abi.TypeSpec` instance available. For example:

.. code-block:: python

    from pyteal import *

    my_uint_type = abi.Uint8TypeSpec()
    my_uint = my_uint_type.new_instance()

    my_array_type = abi.StaticArrayTypeSpec(my_uint_type, 12)
    my_array = my_array_type.new_instance()

With :code:`abi.make`
"""""""""""""""""""""

Using :code:`abi.TypeSpec.new_instance()` makes sense if you already have an instance of the right :any:`abi.TypeSpec`, but otherwise it's not much better than using the constructor. Because of this, we have the :any:`abi.make` method, which is perhaps the most convenient way to create a compound type.

To use it, you pass in a `PEP 484 <https://peps.python.org/pep-0484/>`__ Python type annotation that describes the ABI type, and :any:`abi.make` will create an instance of it for you. For example:

.. code-block:: python

    from typing import Literal
    from pyteal import *

    my_uint8 = abi.make(abi.Uint8)
    my_uint64 = abi.make(abi.Uint64)
    my_array = abi.make(abi.StaticArray[abi.Uint8, Literal[12]])

.. note::
    Since Python does not allow integers to be directly embedded in type annotations, you must wrap any integer arguments in the :code:`Literal` annotation from the :code:`typing` module.

.. _Computed Values:

Computed Values
^^^^^^^^^^^^^^^^^^^^^^^

With the introduction of ABI types, it's only natural for there to be functions and operations which return ABI values. In a conventional language, it would be enough to return an instance of the type directly from the operation. However, in PyTeal, these operations must actually return two values:

1. An instance of the ABI type that will be populated with the right value
2. An :code:`Expr` object that contains the expressions necessary to compute and populate the value that the return type should have

In order to combine these two pieces of information, the :any:`abi.ComputedValue[T] <abi.ComputedValue>` interface was introduced. Instead of directly returning an instance of the appropriate ABI type, functions that return ABI values will return an :any:`abi.ComputedValue` instance parameterized by the return type.

For example, the :any:`abi.Tuple.__getitem__` function does not return an :any:`abi.BaseType`; instead, it returns an :code:`abi.TupleElement[abi.BaseType]` instance, which inherits from :code:`abi.ComputedValue[abi.BaseType]`.

The :any:`abi.ComputedValue[T] <abi.ComputedValue>` abstract base class provides the following methods:

* :any:`abi.ComputedValue[T].produced_type_spec() <abi.ComputedValue.produced_type_spec>`: returns the :any:`abi.TypeSpec` representing the ABI type produced by this object.
* :any:`abi.ComputedValue[T].store_into(output: T) <abi.ComputedValue.store_into>`: computes the value and store it into the ABI type instance :code:`output`.
* :any:`abi.ComputedValue[T].use(action: Callable[[T], Expr]) <abi.ComputedValue.use>`: computes the value and passes it to the callable expression :code:`action`. This is offered as a convenience over the :code:`store_into(...)` method if you don't want to create a new variable to store the value before using it.

.. note::
    If you call the methods :code:`store_into(...)` or :code:`use(...)` multiple times, the computation to determine the value will be repeated each time. For this reason, it's recommended to only issue a single call to either of these two methods.

A brief example is below:

.. code-block:: python

    from typing import Literal as L
    from pyteal import *

    @Subroutine(TealType.none)
    def assert_sum_equals(
        array: abi.StaticArray[abi.Uint64, L[10]], expected_sum: Expr
    ) -> Expr:
        """This subroutine asserts that the sum of the elements in `array` equals `expected_sum`"""
        i = ScratchVar(TealType.uint64)
        actual_sum = ScratchVar(TealType.uint64)
        tmp_value = abi.Uint64()
        return Seq(
            For(i.store(Int(0)), i.load() < array.length(), i.store(i.load() + Int(1))).Do(
                If(i.load() <= Int(5))
                # Both branches of this If statement are equivalent
                .Then(
                    # This branch showcases how to use `store_into`
                    Seq(
                        array[i.load()].store_into(tmp_value),
                        actual_sum.store(actual_sum.load() + tmp_value.get()),
                    )
                ).Else(
                    # This branch showcases how to use `use`
                    array[i.load()].use(
                        lambda value: actual_sum.store(actual_sum.load() + value.get())
                    )
                )
            ),
            Assert(actual_sum.load() == expected_sum),
        )

.. _Type Categories:

Type Categories
~~~~~~~~~~~~~~~~~~~~

There are three categories of ABI types:

#. :ref:`Basic Types`
#. :ref:`Reference Types`
#. :ref:`Transaction Types`

Each of which is described in detail in the following subsections.

.. _Basic Types:

Basic Types
^^^^^^^^^^^^^^^^^^^^^^^^

Basic types are the most straightforward category of ABI types. These types are used to hold values and they have no other special meaning, in contrast to the other categories of types.

Definitions
"""""""""""""""""""""

PyTeal supports the following basic types:

============================================== ====================== =================================== =======================================================================================================================================================
PyTeal Type                                    ARC-4 Type             Dynamic / Static                    Description
============================================== ====================== =================================== =======================================================================================================================================================
:any:`abi.Uint8`                               :code:`uint8`          Static                              An 8-bit unsigned integer
:any:`abi.Uint16`                              :code:`uint16`         Static                              A 16-bit unsigned integer
:any:`abi.Uint32`                              :code:`uint32`         Static                              A 32-bit unsigned integer
:any:`abi.Uint64`                              :code:`uint64`         Static                              A 64-bit unsigned integer
:any:`abi.Bool`                                :code:`bool`           Static                              A boolean value that can be either 0 or 1
:any:`abi.Byte`                                :code:`byte`           Static                              An 8-bit unsigned integer. This is an alias for :code:`abi.Uint8` that should be used to indicate non-numeric data, such as binary arrays.
:any:`abi.StaticArray[T,N] <abi.StaticArray>`  :code:`T[N]`           Static when :code:`T` is static     A fixed-length array of :code:`T` with :code:`N` elements
:any:`abi.Address`                             :code:`address`        Static                              A 32-byte Algorand address. This is an alias for :code:`abi.StaticArray[abi.Byte, Literal[32]]`.
:any:`abi.StaticBytes[N] <abi.StaticBytes>`    :code:`byte[N]`        Static                              A fixed-length array with :code:`N` elements of :code:`abi.Byte`.
:any:`abi.DynamicArray[T] <abi.DynamicArray>`  :code:`T[]`            Dynamic                             A variable-length array of :code:`T`
:any:`abi.DynamicBytes`                        :code:`byte[]`         Dynamic                             A variable-length array of :code:`abi.Byte`.
:any:`abi.String`                              :code:`string`         Dynamic                             A variable-length byte array assumed to contain UTF-8 encoded content. This is an alias for :code:`abi.DynamicArray[abi.Byte]`.
:any:`abi.Tuple`\*, :any:`abi.NamedTuple`      :code:`(...)`          Static when all elements are static A tuple of multiple types
============================================== ====================== =================================== =======================================================================================================================================================

.. note::
    \*A proper implementation of :any:`abi.Tuple` requires a variable amount of generic arguments. Python 3.11 will support this with the introduction of `PEP 646 - Variadic Generics <https://peps.python.org/pep-0646/>`_, but until then it will not be possible to make :any:`abi.Tuple` a generic type. As a workaround, we have introduced the following subclasses of :any:`abi.Tuple` for tuples containing up to 5 generic arguments:

    * :any:`abi.Tuple0`: a tuple of zero values, :code:`()`
    * :any:`abi.Tuple1[T1] <abi.Tuple1>`: a tuple of one value, :code:`(T1)`
    * :any:`abi.Tuple2[T1,T2] <abi.Tuple2>`: a tuple of two values, :code:`(T1,T2)`
    * :any:`abi.Tuple3[T1,T2,T3] <abi.Tuple3>`: a tuple of three values, :code:`(T1,T2,T3)`
    * :any:`abi.Tuple4[T1,T2,T3,T4] <abi.Tuple4>`: a tuple of four values, :code:`(T1,T2,T3,T4)`
    * :any:`abi.Tuple5[T1,T2,T3,T4,T5] <abi.Tuple5>`: a tuple of five values, :code:`(T1,T2,T3,T4,T5)`

    While we are still on PyTeal 3.10, we have a workaround for :any:`abi.Tuple` by :any:`abi.NamedTuple`, which allows one to define a tuple with more than 5 generic arguments, and access tuple elements by field name. For example:

    .. code-block:: python

        from pyteal import *
        from typing import Literal as L

        class InheritedFromNamedTuple(abi.NamedTuple):
            acct_address: abi.Field[abi.Address]
            amount: abi.Field[abi.Uint64]
            retrivable: abi.Field[abi.Bool]
            desc: abi.Field[abi.String]
            list_of_addrs: abi.Field[abi.DynamicArray[abi.Address]]
            balance_list: abi.Field[abi.StaticArray[abi.Uint64, L[10]]]

These ARC-4 types are not yet supported in PyTeal:

* Non-power-of-2 unsigned integers under 64 bits, i.e. :code:`uint24`, :code:`uint48`, :code:`uint56`
* Unsigned integers larger than 64 bits
* Fixed point unsigned integers, i.e. :code:`ufixed<N>x<M>`

Limitations
"""""""""""""""""""""

Due to the nature of their encoding, dynamic container types, i.e. :any:`abi.DynamicArray[T] <abi.DynamicArray>` and :any:`abi.String`, have an implicit limit on the number of elements they may contain. This limit is :code:`2^16 - 1`, or 65535. However, the AVM has a stack size limit of 4096 for byte strings, so it's unlikely this encoding limit will be reached by your program.

Static container types have no such limit.

Usage
"""""""""""""""""""""

Setting Values
''''''''''''''''

All basic types have a :code:`set()` method which can be used to assign a value. The arguments for this method differ depending on the ABI type. For convenience, here are links to the docs for each class's method:

* :any:`abi.Uint.set(...) <abi.Uint.set>`, which is used by all :code:`abi.Uint` classes and :code:`abi.Byte`
* :any:`abi.Bool.set(...) <abi.Bool.set>`
* :any:`abi.StaticArray[T, N].set(...) <abi.StaticArray.set>`
* :any:`abi.Address.set(...) <abi.Address.set>`
* :any:`abi.StaticBytes[N].set(...) <abi.StaticBytes.set>`
* :any:`abi.DynamicArray[T].set(...) <abi.DynamicArray.set>`
* :any:`abi.DynamicBytes.set(...) <abi.DynamicBytes.set>`
* :any:`abi.String.set(...) <abi.String.set>`
* :any:`abi.Tuple.set(...) <abi.Tuple.set>`

A brief example is below. Please consult the documentation linked above for each method to learn more about specific usage and behavior.

.. code-block:: python

    from pyteal import *

    my_address = abi.make(abi.Address)
    my_bool = abi.make(abi.Bool)
    my_uint64 = abi.make(abi.Uint64)
    my_tuple = abi.make(abi.Tuple3[abi.Address, abi.Bool, abi.Uint64])

    program = Seq(
        my_address.set(Txn.sender()),
        my_bool.set(Txn.fee() == Int(0)),
        # It's ok to set an abi.Uint to a Python integer. This is actually preferred since PyTeal
        # can determine at compile-time that the value will fit in the integer type.
        my_uint64.set(5000),
        my_tuple.set(my_address, my_bool, my_uint64)
    )

Getting Single Values
''''''''''''''''''''''

All basic types that represent a single value have a :code:`get()` method, which can be used to extract that value. The supported types and methods are:

* :any:`abi.Uint.get()`, which is used by all :any:`abi.Uint` classes and :any:`abi.Byte`
* :any:`abi.Bool.get()`
* :any:`abi.Address.get()`
* :any:`abi.String.get()`

A brief example is below. Please consult the documentation linked above for each method to learn more about specific usage and behavior.

.. code-block:: python

    from pyteal import *

    @Subroutine(TealType.uint64)
    def minimum(a: abi.Uint64, b: abi.Uint64) -> Expr:
        """Return the minimum value of the two arguments."""
        return (
            If(a.get() < b.get())
            .Then(a.get())
            .Else(b.get())
        )

Getting Values at Indexes - Compound Types
''''''''''''''''''''''''''''''''''''''''''

The types :any:`abi.StaticArray`, :any:`abi.Address`, :any:`abi.DynamicArray`, :any:`abi.String`, and :any:`abi.Tuple` are compound types, meaning they contain other types whose values can be extracted. The :code:`__getitem__` method, accessible by using square brackets to "index into" an object, can be used to access these values.

The supported methods are:

* :any:`abi.StaticArray.__getitem__(index: int | Expr) <abi.StaticArray.__getitem__>`, used for :any:`abi.StaticArray` and :any:`abi.Address`
* :any:`abi.Array.__getitem__(index: int | Expr) <abi.Array.__getitem__>`, used for :any:`abi.DynamicArray` and :any:`abi.String`
* :any:`abi.Tuple.__getitem__(index: int) <abi.Tuple.__getitem__>`, used for :any:`abi.Tuple` and :any:`abi.NamedTuple`\*

.. note::
    Be aware that these methods return a :any:`ComputedValue`, similar to other PyTeal operations which return ABI types. More information about why that is necessary and how to use a :any:`ComputedValue` can be found in the :ref:`Computed Values` section.

.. note::
    \*For :any:`abi.NamedTuple`, one can access tuple elements through both methods

    * :any:`abi.Tuple.__getitem__(index: int) <abi.Tuple.__getitem__>`
    * :any:`abi.NamedTuple.__getattr__(name: str) <abi.NamedTuple.__getattr__>`

A brief example is below. Please consult the documentation linked above for each method to learn more about specific usage and behavior.

.. code-block:: python

    from typing import Literal as L
    from pyteal import *

    @Subroutine(TealType.none)
    def ensure_all_values_greater_than_5(array: abi.StaticArray[abi.Uint64, L[10]]) -> Expr:
        """This subroutine asserts that every value in the input array is greater than 5."""
        i = ScratchVar(TealType.uint64)
        return For(
            i.store(Int(0)), i.load() < array.length(), i.store(i.load() + Int(1))
        ).Do(
            array[i.load()].use(lambda value: Assert(value.get() > Int(5)))
        )

.. _Reference Types:

Reference Types
^^^^^^^^^^^^^^^^^^^^^^^^

Many applications require the caller to provide "foreign array" values when calling the app. These are the blockchain entities (such as accounts, assets, or other applications) that the application will interact with when executing this call. In the ABI, we have **Reference Types** to describe these requirements.

Definitions
""""""""""""""""""""""""""""""""""""""""""

PyTeal supports the following Reference Types:

====================== ====================== ================ =======================================================================================================================================================
PyTeal Type            ARC-4 Type             Dynamic / Static Description
====================== ====================== ================ =======================================================================================================================================================
:any:`abi.Account`     :code:`account`        Static           Represents an account that the current transaction can access, stored in the :any:`Txn.accounts <TxnObject.accounts>` array
:any:`abi.Asset`       :code:`asset`          Static           Represents an asset that the current transaction can access, stored in the :any:`Txn.assets <TxnObject.assets>` array
:any:`abi.Application` :code:`application`    Static           Represents an application that the current transaction can access, stored in the :any:`Txn.applications <TxnObject.applications>` array
====================== ====================== ================ =======================================================================================================================================================

These types all inherit from the abstract class :any:`abi.ReferenceType`.

Limitations
""""""""""""""""""""""""""""""""""""""""""

Because References Types have a special meaning, they should not be directly created, and they cannot be assigned a value by a program.

Additionally, Reference Types are only valid in the arguments of a method. They may not appear in a method's return value.

Note that the AVM has `limitations on the maximum number of foreign references <https://developer.algorand.org/docs/get-details/parameter_tables/#smart-contract-constraints>`_ an application call transaction may contain. At the time of writing, these limits are:

* Accounts: 4
* Assets: 8
* Applications: 8
* Sum of Accounts, Assets, and Applications: 8

.. warning::
    Because of these limits, methods that have a large amount of Reference Type arguments may be impossible to call as intended at runtime.

Usage
""""""""""""""""""""""""""""""""""""""""""

Getting Referenced Values
''''''''''''''''''''''''''

Depending on the Reference Type, there are different methods available to obtain the value being referenced:

* :any:`abi.Account.address()`
* :any:`abi.Asset.asset_id()`
* :any:`abi.Application.application_id()`

A brief example is below:

.. code-block:: python

    from pyteal import *

    @Subroutine(TealType.none)
    def send_inner_txns(
        receiver: abi.Account, asset_to_transfer: abi.Asset, app_to_call: abi.Application
    ) -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.receiver: receiver.address(),
                    TxnField.xfer_asset: asset_to_transfer.asset_id(),
                    TxnField.amount: Int(1_000_000),
                }
            ),
            InnerTxnBuilder.Submit(),
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.application_id: app_to_call.application_id(),
                    Txn.application_args: [Bytes("hello")],
                }
            ),
            InnerTxnBuilder.Submit(),
        )

Accessing Parameters of Referenced Values
''''''''''''''''''''''''''''''''''''''''''

Reference Types allow the program to access more information about them. Each Reference Type has a :code:`params()` method which can be used to access that object's parameters. These methods are listed below:

* :any:`abi.Account.params()` returns an :any:`AccountParamObject`
* :any:`abi.Asset.params()` returns an :any:`AssetParamObject`
* :any:`abi.Application.params()` returns an :any:`AppParamObject`

These method are provided for convenience. They expose the same properties accessible from the :any:`AccountParam`, :any:`AssetParam`, and :any:`AppParam` classes.

A brief example is below:

.. code-block:: python

    from pyteal import *

    @Subroutine(TealType.none)
    def referenced_params_example(
        account: abi.Account, asset: abi.Asset, app: abi.Application
    ) -> Expr:
        return Seq(
            account.params().auth_address().outputReducer(
                lambda value, has_value: Assert(And(has_value, value == Global.zero_address()))
            ),
            asset.params().total().outputReducer(
                lambda value, has_value: Assert(And(has_value, value == Int(1)))
            ),
            app.params().creator_address().outputReducer(
                lambda value, has_value: Assert(And(has_value, value == Txn.sender()))
            )
        )

.. note::
    All returned parameters are instances of :any:`MaybeValue`, which is why the :any:`outputReducer(...) <MultiValue.outputReducer>` method is used.

Accessing Asset Holdings
''''''''''''''''''''''''

Similar to the parameters above, asset holding properties can be accessed using one of the following methods:

* :any:`abi.Account.asset_holding(asset: Expr | abi.Asset) <abi.Account.asset_holding>`: given an asset, returns an :any:`AssetHoldingObject`
* :any:`abi.Asset.holding(account: Expr | abi.Account) <abi.Asset.holding>`: given an account, returns an :any:`AssetHoldingObject`

These method are provided for convenience. They expose the same properties accessible from the :any:`AssetHolding` class.

A brief example is below:

.. code-block:: python

    from pyteal import *

    @Subroutine(TealType.none)
    def ensure_asset_balance_is_nonzero(account: abi.Account, asset: abi.Asset) -> Expr:
        return Seq(
            account.asset_holding(asset)
            .balance()
            .outputReducer(lambda value, has_value: Assert(And(has_value, value > Int(0)))),
            # this check is equivalent
            asset.holding(account)
            .balance()
            .outputReducer(lambda value, has_value: Assert(And(has_value, value > Int(0)))),
        )

.. _Transaction Types:

Transaction Types
^^^^^^^^^^^^^^^^^^^^^^^^

Some application calls require that they are invoked as part of a larger transaction group containing specific additional transactions. In order to express these types of calls, the ABI has **Transaction Types**.

Every Transaction Type argument represents a specific and unique transaction that must appear immediately before the application call in the same transaction group. A method may have multiple Transaction Type arguments, in which case they must appear in the same order as the method's arguments immediately before the method application call.

Definitions
""""""""""""""""""""""""""""""""""""""""""

PyTeal supports the following Transaction Types:

===================================== ====================== ================ =======================================================================================================================================================
PyTeal Type                           ARC-4 Type             Dynamic / Static Description
===================================== ====================== ================ =======================================================================================================================================================
:any:`abi.Transaction`                :code:`txn`            Static           A catch-all for any type of transaction
:any:`abi.PaymentTransaction`         :code:`pay`            Static           A payment transaction
:any:`abi.KeyRegisterTransaction`     :code:`keyreg`         Static           A key registration transaction
:any:`abi.AssetConfigTransaction`     :code:`acfg`           Static           An asset configuration transaction
:any:`abi.AssetTransferTransaction`   :code:`axfer`          Static           An asset transfer transaction
:any:`abi.AssetFreezeTransaction`     :code:`afrz`           Static           An asset freeze transaction
:any:`abi.ApplicationCallTransaction` :code:`appl`           Static           An application call transaction
===================================== ====================== ================ =======================================================================================================================================================

Limitations
""""""""""""""""""""""""""""""""""""""""""

Due to the special meaning of Transaction Types, they **cannot** be used as the return value of a method. They can be used as method arguments, but only at the top-level. This means that it's not possible to embed a Transaction Type inside a tuple or array.

Transaction Types should not be directly created, and they cannot be modified by a program.

Because the AVM has a maximum of 16 transactions in a single group, at most 15 Transaction Types may be used in the arguments of a method.

Usage
""""""""""""""""""""""""""""""""""""""""""

Getting the Transaction Group Index
''''''''''''''''''''''''''''''''''''

All Transaction Types implement the :any:`abi.Transaction.index()` method, which returns the absolute index of that transaction in the group.

A brief example is below:

.. code-block:: python

    from pyteal import *

    @Subroutine(TealType.none)
    def handle_txn_args(
        any_txn: abi.Transaction,
        pay: abi.PaymentTransaction,
        axfer: abi.AssetTransferTransaction,
    ) -> Expr:
        return Seq(
            Assert(any_txn.index() == Txn.group_index() - Int(3)),
            Assert(pay.index() == Txn.group_index() - Int(2)),
            Assert(axfer.index() == Txn.group_index() - Int(1)),
        )

Accessing Transaction Fields
'''''''''''''''''''''''''''''

All Transaction Types implement the :any:`abi.Transaction.get()` method, which returns a :any:`TxnObject` instance that can be used to access fields from that transaction.

A brief example is below:

.. code-block:: python

    from pyteal import *

    @Subroutine(TealType.none)
    def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:
        """This method receives a payment from an account opted into this app
        and records it in their local state.
        """
        return Seq(
            Assert(payment.get().sender() == sender.address()),
            Assert(payment.get().receiver() == Global.current_application_address()),
            App.localPut(
                sender.address(),
                Bytes("balance"),
                App.localGet(sender.address(), Bytes("balance")) + payment.get().amount(),
            ),
        )


Subroutines with ABI Types
--------------------------

Subroutines can be created that accept ABI types as arguments and produce ABI types as return values. PyTeal will type check all subroutine calls and ensure that the correct types are being passed to such subroutines and that their return values are used correctly.

There are two different ways to use ABI types in subroutines, depending on whether the return value is an ABI type or a PyTeal :code:`Expr`.

Subroutines that Return Expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you'd like to create a subroutine that accepts some or all arguments as ABI types, but whose return value is a PyTeal :code:`Expr`, the :any:`@Subroutine <Subroutine>` decorator can be used.

To indicate the type of each argument, `PEP 484 <https://peps.python.org/pep-0484/>`__ Python type annotations are used. Unlike normal usage of Python type annotations which are ignored at runtime, type annotations for subroutines inform the PyTeal compiler about the inputs and outputs of a subroutine. Changing these values has a direct effect on the code PyTeal generates.

An example of this type of subroutine is below:

.. code-block:: python

    from pyteal import *

    @Subroutine(TealType.uint64)
    def get_volume_of_rectangular_prism(
        length: abi.Uint16, width: abi.Uint64, height: Expr
    ) -> Expr:
        return length.get() * width.get() * height

Notice that this subroutine accepts the following arguments, not all of which are ABI types:

* :code:`length`: an ABI :any:`abi.Uint16` type
* :code:`width`: an ABI :any:`abi.Uint64` type
* :code:`height`: a PyTeal :any:`Expr` type

Despite some inputs being ABI types, calling this subroutine works the same as usual, except the values for the ABI type arguments must be the appropriate ABI type.

The following example shows how to prepare the arguments for and call :code:`get_volume_of_rectangular_prism()`:

.. code-block:: python

    # This is a continuation of the previous example

    length = abi.Uint16()
    width = abi.Uint64()
    height = Int(10)
    program = Seq(
        length.set(4),
        width.set(9),
        Assert(get_volume_of_rectangular_prism(length, width, height) > Int(0))
    )

Subroutines that Return ABI Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::
    :any:`ABIReturnSubroutine` is still taking shape and is subject to backwards incompatible changes.

    * For ABI Application entry point definition, feel encouraged to use :any:`ABIReturnSubroutine`. Expect a best-effort attempt to minimize backwards incompatible changes along with a migration path.
    * For general purpose usage, use at your own risk. Based on feedback, the API and usage patterns will change more freely and with less effort to provide migration paths.

    For these reasons, we strongly recommend using :any:`pragma` or the :any:`Pragma` expression to pin the version of PyTeal in your source code. See :ref:`version pragmas` for more information.

In addition to accepting ABI types as arguments, it's also possible for a subroutine to return an ABI type value.

As mentioned in the :ref:`Computed Values` section, operations which return ABI values instead of traditional :code:`Expr` objects need extra care. In order to solve this problem for subroutines, a new decorator, :any:`@ABIReturnSubroutine <ABIReturnSubroutine>` has been introduced.

The :code:`@ABIReturnSubroutine` decorator should be used with subroutines that return an ABI value. Subroutines defined with this decorator will have two places to output information: the function return value, and a `keyword-only argument <https://peps.python.org/pep-3102/>`_ called :code:`output`. The function return value must remain an :code:`Expr`, while the :code:`output` keyword argument will contain the ABI value the subroutine wishes to return. An example is below:

.. code-block:: python

    from pyteal import *

    @ABIReturnSubroutine
    def get_account_status(
        account: abi.Address, *, output: abi.Tuple2[abi.Uint64, abi.Bool]
    ) -> Expr:
        balance = abi.Uint64()
        is_admin = abi.Bool()
        return Seq(
            balance.set(App.localGet(account.get(), Bytes("balance"))),
            is_admin.set(App.localGet(account.get(), Bytes("is_admin"))),
            output.set(balance, is_admin),
        )

    account = abi.make(abi.Address)
    status = abi.make(abi.Tuple2[abi.Uint64, abi.Bool])
    program = Seq(
        account.set(Txn.sender()),
        # NOTE! The return value of get_account_status(account) is actually a ComputedValue[abi.Tuple2[abi.Uint64, abi.Bool]]
        get_account_status(account).store_into(status),
    )

Notice that even though the original :code:`get_account_status` function returns an :code:`Expr` object, the :code:`@ABIReturnSubroutine` decorator automatically transforms the function's return value and the :code:`output` variable into a :code:`ComputedValue`. As a result, callers of this subroutine must work with a :code:`ComputedValue`.

The only exception to this transformation is if the subroutine has no return value. Without a return value, a :code:`ComputedValue` is unnecessary and the subroutine will still return an :code:`Expr` to the caller. In this case, the :code:`@ABIReturnSubroutine` decorator acts identically the :code:`@Subroutine` decorator.

The name of the subroutine constructed by the :code:`@ABIReturnSubroutine` decorator is by default the function name. In order to override the default subroutine name, the decorator :any:`ABIReturnSubroutine.name_override <ABIReturnSubroutine.name_override>` is introduced to construct a subroutine with its name overridden. An example is below:

.. code-block:: python

    from pyteal import *

    @ABIReturnSubroutine.name_override("increment")
    def add_by_one(prev: abi.Uint32, *, output: abi.Uint32) -> Expr:
        return output.set(prev.get() + Int(1))

    # NOTE! In this case, the `ABIReturnSubroutine` is initialized with a name "increment"
    #       overriding its original name "add_by_one"
    assert add_by_one.method_spec().dictify()["name"] == "increment"


Creating an ARC-4 Program
----------------------------------------------------

An ARC-4 program, like all other programs, can be called by application call transactions. ARC-4 programs respond to two specific subtypes of application call transactions:

* **Method calls**, which encode a specific method to be called and arguments for that method, if needed.
* **Bare app calls**, which have no arguments and no return value.

A method is a section of code intended to be invoked externally with an application call transaction. Methods may take arguments and may produce a return value. PyTeal implements methods as subroutines which are exposed to be externally callable.

A bare app call is more limited than a method, since it takes no arguments and cannot return a value. For this reason, bare app calls are more suited to allow on completion actions to take place, such as opting into an app.

To make it easier for an application to route across the many bare app calls and methods it may support, PyTeal introduces the :any:`Router` class. This class adheres to the ARC-4 ABI conventions with respect to when methods and bare app calls should be invoked. For methods, it also conveniently decodes all arguments and properly encodes and logs the return value as needed.

The following sections explain how to register bare app calls and methods with the :any:`Router` class.

.. warning::
    :any:`Router` usage is still taking shape and is subject to backwards incompatible changes.

    Feel encouraged to use :any:`Router` and expect a best-effort attempt to minimize backwards incompatible changes along with a migration path.

    For these reasons, we strongly recommend using :any:`pragma` or the :any:`Pragma` expression to pin the version of PyTeal in your source code. See :ref:`version pragmas` for more information.

Registering Bare App Calls
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The AVM supports 6 types of OnCompletion options that may be specified on an app call transaction. These actions are:

#. **No-op**, the absence of an action, represented by :any:`OnComplete.NoOp`
#. **Opt in**, which allocates account-local storage for an app, represented by :any:`OnComplete.OptIn`
#. **Close out**, which removes account-local storage for an app, represented by :any:`OnComplete.CloseOut`
#. **Clear state**, which forcibly removes account-local storage for an app, represented by :any:`OnComplete.ClearState`
#. **Update application**, which updates an app, represented by :any:`OnComplete.UpdateApplication`
#. **Delete application**, which deletes an app, represented by :any:`OnComplete.DeleteApplication`

.. note::
    While **clear state** is a valid OnCompletion action, its behavior differs significantly from the others. For this reason, the :any:`Router` does not support bare app calls or methods to be called during clear state. Instead, you may use the :code:`clear_state` argument in :any:`Router.__init__` to do work during clear state.

In PyTeal, you have the ability to register a bare app call handler for each of these actions, except for clear state. Additionally, a bare app call handler must also specify whether the handler can be invoking during an **app creation transaction** (:any:`CallConfig.CREATE`), during a **non-creation app call** (:any:`CallConfig.CALL`), or during **either** (:any:`CallConfig.ALL`).

The :any:`BareCallActions` class is used to define a bare app call handler for on completion actions. Each bare app call handler must be an instance of the :any:`OnCompleteAction` class.

The :any:`OnCompleteAction` class is responsible for holding the actual code for the bare app call handler (an instance of either :code:`Expr` or a subroutine that takes no args and returns nothing) as well as a :any:`CallConfig` option that indicates whether the action is able to be called during a creation app call, a non-creation app call, or either.

All the bare app calls that an application wishes to support must be provided to the :any:`Router.__init__` method. Additionally, if you wish to perform actions during clear state, you can specify the :code:`clear_state` argument.

A brief example is below:

.. code-block:: python

    from pyteal import *

    @Subroutine(TealType.none)
    def opt_in_handler() -> Expr:
        return App.localPut(Txn.sender(), Bytes("opted_in_round"), Global.round())


    @Subroutine(TealType.none)
    def assert_sender_is_creator() -> Expr:
        return Assert(Txn.sender() == Global.creator_address())


    router = Router(
        name="ExampleApp",
        bare_calls=BareCallActions(
            # Allow app creation with a no-op action
            no_op=OnCompleteAction(
                action=Approve(), call_config=CallConfig.CREATE
            ),

            # Register the `opt_in_handler` to be called during opt in.
            #
            # Since we use `CallConfig.ALL`, this is also a valid way to create this app
            # (if the creator wishes to immediately opt in).
            opt_in=OnCompleteAction(
                action=opt_in_handler, call_config=CallConfig.ALL
            ),

            # Allow anyone who opted in to close out from the app.
            close_out=OnCompleteAction(
                action=Approve(), call_config=CallConfig.CALL
            ),

            # Only approve update and delete operations if `assert_sender_is_creator` succeeds.
            update_application=OnCompleteAction(
                action=assert_sender_is_creator, call_config=CallConfig.CALL
            ),
            delete_application=OnCompleteAction(
                action=assert_sender_is_creator, call_config=CallConfig.CALL
            ),
        ),
        clear_state=Approve(),
    )

.. note::
    When deciding which :any:`CallConfig` value is appropriate for a bare app call or method, consider the question, should it be valid for someone to create my app with this operation? Most of the time the answer will be no, in which case :any:`CallConfig.CALL` should be used.

Registering Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::
    The :any:`Router` **does not** validate inputs for compound types (:any:`abi.StaticArray`, :any:`abi.Address`, :any:`abi.DynamicArray`, :any:`abi.String`, or :any:`abi.Tuple`).

    **We strongly recommend** methods immediately access and validate compound type parameters *before* persisting arguments for later transactions. For validation, it is sufficient to attempt to extract each element your method will use. If there is an input error for an element, indexing into that element will fail.

    Notes:

    * This recommendation applies to recursively contained compound types as well. Successfully extracting an element which is a compound type does not guarantee the extracted value is valid; you must also inspect its elements as well.
    * Because of this, :any:`abi.Address` is **not** guaranteed to have exactly 32 bytes. To defend against unintended behavior, manually verify the length is 32 bytes, i.e. :code:`Assert(Len(address.get()) == Int(32))`.

There are two ways to register a method with the :any:`Router` class.

The first way to register a method is with the :any:`Router.add_method_handler` method, which takes an existing subroutine decorated with :any:`@ABIReturnSubroutine <ABIReturnSubroutine>`. An example of this is below:

.. code-block:: python

    from pyteal import *

    router = Router(
        name="Calculator",
        bare_calls=BareCallActions(
            # Allow this app to be created with a no-op call
            no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE),
            # Allow standalone user opt in and close out
            opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.CALL),
            close_out=OnCompleteAction(action=Approve(), call_config=CallConfig.CALL),
        ),
        clear_state=Approve(),
    )

    @ABIReturnSubroutine
    def add(a: abi.Uint64, b: abi.Uint64, *, output: abi.Uint64) -> Expr:
        """Adds the two arguments and returns the result.

        If addition will overflow a uint64, this method will fail.
        """
        return output.set(a.get() + b.get())


    @ABIReturnSubroutine
    def addAndStore(a: abi.Uint64, b: abi.Uint64, *, output: abi.Uint64) -> Expr:
        """Adds the two arguments, returns the result, and stores it in the sender's local state.

        If addition will overflow a uint64, this method will fail.

        The sender must be opted into the app. Opt-in can occur during this call.
        """
        return Seq(
            output.set(a.get() + b.get()),
            # store the result in the sender's local state too
            App.localPut(Txn.sender(), Bytes("result", output.get())),
        )

    # Register the `add` method with the router, using the default `MethodConfig`
    # (only no-op, non-creation calls allowed).
    router.add_method_handler(add)

    # Register the `addAndStore` method with the router, using a `MethodConfig` that allows
    # no-op and opt in non-creation calls.
    router.add_method_handler(
        addAndStore,
        method_config=MethodConfig(no_op=CallConfig.CALL, opt_in=CallConfig.CALL),
    )

This example registers two methods with the router, :code:`add` and :code:`addAndStore`.

Because the :code:`add` method does not pass a value for the :code:`method_config` parameter of :any:`Router.add_method_handler`, it will use the default value, which will make it only callable with a transaction that is not an app creation and whose on completion value is :code:`OnComplete.NoOp`.

On the other hand, the :code:`addAndStore` method does provide a :code:`method_config` value. A value of :code:`MethodConfig(no_op=CallConfig.CALL, opt_in=CallConfig.CALL)` indicates that this method can only be called with a transaction that is not an app creation and whose on completion value is one of :code:`OnComplete.NoOp` or :code:`OnComplete.OptIn`.

The second way to register a method is with the :any:`Router.method` decorator placed directly on a function. This way is equivalent to the first, but has some properties that make it more convenient for some scenarios. Below is an example equivalent to the prior one, but using the :code:`Router.method` syntax:

.. code-block:: python

    from pyteal import *

    my_router = Router(
        name="Calculator",
        bare_calls=BareCallActions(
            # Allow this app to be created with a no-op call
            no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE),
            # Allow standalone user opt in and close out
            opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.CALL),
            close_out=OnCompleteAction(action=Approve(), call_config=CallConfig.CALL),
        ),
    )

    # NOTE: the first part of the decorator `@my_router.method` is the router variable's name
    @my_router.method
    def add(a: abi.Uint64, b: abi.Uint64, *, output: abi.Uint64) -> Expr:
        """Adds the two arguments and returns the result.

        If addition will overflow a uint64, this method will fail.
        """
        return output.set(a.get() + b.get())

    @my_router.method(no_op=CallConfig.CALL, opt_in=CallConfig.CALL)
    def addAndStore(a: abi.Uint64, b: abi.Uint64, *, output: abi.Uint64) -> Expr:
        """Adds the two arguments, returns the result, and stores it in the sender's local state.

        If addition will overflow a uint64, this method will fail.

        The sender must be opted into the app. Opt-in can occur during this call.
        """
        return Seq(
            output.set(a.get() + b.get()),
            # store the result in the sender's local state too
            App.localPut(Txn.sender(), Bytes("result", output.get())),
        )

Compiling a Router Program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that we know how to add bare app call and method call handlers to a :any:`Router`, the next step is to compile the :any:`Router` into TEAL code.

The :any:`Router.compile_program` method exists for this purpose. It combines all registered methods and bare app calls into two ASTs, one for the approval program and one for clear state program, then internally calls :any:`compileTeal` to compile these expressions and create TEAL code.

.. note::
    We recommend enabling the :code:`scratch_slots` optimization when compiling a program that uses ABI types, since PyTeal's ABI types implementation makes frequent use of scratch slots under-the-hood. See the :ref:`compiler_optimization` page for more information.

In addition to receiving the approval and clear state programs, the :any:`Router.compile_program` method also returns a `Python SDK <https://py-algorand-sdk.readthedocs.io/en/latest/algosdk/abi/contract.html#algosdk.abi.contract.Contract>`_ :code:`Contract` object. This object represents an `ARC-4 Contract Description <https://arc.algorand.foundation/ARCs/arc-0004#contract-description>`_, which can be distributed to clients to enable them to call the methods on the contract.

Here's an example of a complete application that uses the :any:`Router` class:

.. literalinclude:: ../examples/application/abi/algobank.py
    :language: python

This example uses the :code:`Router.compile_program` method to create the approval program, clear state program, and contract description for the "AlgoBank" contract. The produced :code:`algobank.json` file is below:

.. literalinclude:: ../examples/application/abi/algobank.json
    :language: json

Calling an ARC-4 Program
--------------------------

One of the advantages of developing an ABI-compliant PyTeal contract is that there is a standard way for clients to call your contract.

Broadly, there are two categories of clients that may wish to call your contract: off-chain systems and other on-chain contracts. The following sections describe how each of these clients can call ABI methods implemented by your contract.

Off-Chain, from an SDK or :code:`goal`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Off-chain systems can use the `Algorand SDKs <https://developer.algorand.org/docs/sdks/>`_ or the command-line tool `goal <https://developer.algorand.org/docs/clis/goal/goal/>`_ to interact with ABI-compliant contracts.

Every SDK contains an :code:`AtomicTransactionComposer` type that can be used to build and execute transaction groups, including groups containing ABI method calls. More information and examples of this are available on the `Algorand Developer Portal <https://developer.algorand.org/docs/get-details/atc/>`_.

The :code:`goal` CLI has subcommands for creating and submitting various types of transactions. The relevant ones for ABI-compliant contracts are mentioned below:

* For bare app calls:
    * For calls that create an app, :code:`goal app create` (`docs <https://developer.algorand.org/docs/clis/goal/app/create/>`__) can be used to construct and send an app creation bare app call.
    * For non-creation calls, :code:`goal app <action>` can be used to construct and send a non-creation bare app call. The :code:`<action>` keyword should be replaced with one of `"call" <https://developer.algorand.org/docs/clis/goal/app/call/>`_ (no-op), `"optin" <https://developer.algorand.org/docs/clis/goal/app/optin/>`_, `"closeout" <https://developer.algorand.org/docs/clis/goal/app/closeout/>`_, `"clear" <https://developer.algorand.org/docs/clis/goal/app/clear/>`_, `"update" <https://developer.algorand.org/docs/clis/goal/app/update/>`_, or `"delete" <https://developer.algorand.org/docs/clis/goal/app/delete/>`_, depending on the on-completion value the caller wishes to use.
* For all method calls:
    * :code:`goal app method` (`docs <https://developer.algorand.org/docs/clis/goal/app/method/>`__) can be used to construct, send, and read the return value of a method call. This command can be used for application creation as well, if the application allows this to happen in one of its methods.

On-Chain, in an Inner Transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Algorand applications can issue `inner transactions <https://developer.algorand.org/docs/get-details/dapps/smart-contracts/apps/#issuing-transactions-from-an-application>`_, which can be used to invoke other applications.

In PyTeal, this can be achieved using the :any:`InnerTxnBuilder` class and its functions. To invoke an ABI method, PyTeal has :any:`InnerTxnBuilder.MethodCall(...) <InnerTxnBuilder.MethodCall>` to properly build a method call and encode its arguments.

.. note::
    At the time of writing, there is no streamlined way to obtain a method return value. You must manually inspect the :any:`last_log() <TxnObject.last_log>` property of either :any:`InnerTxn` or :any:`Gitxn[\<index\>] <Gitxn>` to obtain the logged return value. `As described in ARC-4 <https://arc.algorand.foundation/ARCs/arc-0004#standard-format>`_, this value will be prefixed with the 4 bytes :code:`151f7c75` (shown in hex), and after this prefix the encoded ABI value will be available. You can use the :any:`decode(...) <abi.BaseType.decode>` method on an instance of the appropriate ABI type in order to decode and use this value.
