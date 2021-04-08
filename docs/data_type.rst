.. _data-type:

Data Types and Constants
========================

A PyTeal expression has one of the following two data types:

 * :any:`TealType.uint64`, 64 bit unsigned integer
 * :any:`TealType.bytes`, a slice of bytes

For example, all the transaction arguments (e.g. :code:`Arg(0)`) are of type :any:`TealType.bytes`.
The first valid round of current transaction (:any:`Txn.first_valid() <TxnObject.first_valid()>`) is typed :any:`TealType.uint64`.

Integers
--------

:code:`Int(n)` creates a :code:`TealType.uint64` constant, where :code:`n >= 0 and n < 2 ** 64`.

Bytes
-----

A byte slice is a binary string. There are several ways to encode a byte slice in PyTeal:

UTF-8
~~~~~

Byte slices can be created from UTF-8 encoded strings. For example:

.. code-block:: Python

    Bytes("hello world")

Base16
~~~~~~

Byte slices can be created from a :rfc:`4648#section-8` base16 encoded
binary string, e.g. :code:`"0xA21212EF"` or :code:`"A21212EF"`. For example:

.. code-block:: Python

    Bytes("base16", "0xA21212EF")
    Bytes("base16", "A21212EF") # "0x" is optional

Base32
~~~~~~

Byte slices can be created from a :rfc:`4648#section-6` base32 encoded
binary string with or without padding, e.g. :code:`"7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M"`.

.. code-block:: Python

    Bytes("base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")

Base64
~~~~~~

Byte slices can be created from a :rfc:`4648#section-4` base64 encoded
binary string, e.g. :code:`"Zm9vYmE="`.

.. code-block:: Python

    Bytes("base64", "Zm9vYmE=")

Type Checking
-------------

All PyTeal expressions are type checked at construction time, for example, running
the following code triggers a :code:`TealTypeError`:  ::

  Int(0) < Arg(0)

Since :code:`<` (overloaded Python operator, see :ref:`arithmetic_expressions` for more details)
requires both operands of type :code:`TealType.uint64`,
while :code:`Arg(0)` is of type :code:`TealType.bytes`.

Conversion
----------

Converting a value to its corresponding value in the other data type is supported by the following two operators:

 * :any:`Itob(n) <Itob>`: generate a :code:`TealType.bytes` value from a :code:`TealType.uint64` value :code:`n`
 * :any:`Btoi(b) <Btoi>`: generate a :code:`TealType.uint64` value from a :code:`TealType.bytes` value :code:`b`

**Note:** These operations are **not** meant to convert between human-readable strings and numbers.
:code:`Itob` produces a big-endian 8-byte encoding of an unsigned integer, not a human readable
string. For example, :code:`Itob(Int(1))` will produce the string :code:`"\x00\x00\x00\x00\x00\x00\x00\x01"`
not the string :code:`"1"`.
