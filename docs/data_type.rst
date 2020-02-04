.. _data-type:

Data Types and Constants
========================

A PyTeal expression has one of the following two data types:

 * :code:`TealType.uint64`, 64 bit unsigned integer
 * :code:`TealType.bytes`, a slice of bytes


For example, all the transaction arguments (e.g. :code:`Arg(0)`) are of type :code:`TealType.bytes`.
The first valid round of current transaction (:code:`Txn.first_valid()`) is typed :code:`TealType.uint64`.

:code:`Int(n)` creates a :code:`TealType.uint64` constant, where :code:`n >= 0 and n < 2 ** 64`.

:code:`Bytes(encoding, value)` creates a :code:`TealType.bytes` constant, where :code:`encoding` could be either
of the following:

 * :code:`"base16"`: its paired :code:`value` needs to be a `RFC 4648 <https://tools.ietf.org/html/rfc4648>`_ base16 encoded string, e.g. :code:`"0xA21212EF"` or
   :code:`"A21212EF"`
 * :code:`"base32"`: its paired :code:`value` needs to be a RFC 4648 base32 encoded string **without padding**, e.g. :code:`"7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M"`
 * :code:`"base64"`: its paired :code:`value` needs to be a RFC 4648 base64 encoded string, e.g. :code:`"Zm9vYmE="`

All PyTeal expressions are type checked at construction time, for example, running
the following code triggers a :code:`TealTypeError`:  ::

  Int(0) < Arg(0)

Since :code:`<` (overloaded Python operator, see :ref:`arithmetic_expressions` for more details)
requires both operands of type :code:`TealType.uint64`,
while :code:`Arg(0)` is of type :code:`TealType.bytes`.

Converting a value to its corresponding value in the other data type is supported by the following two operators:

 * :code:`Itob(n)`: generate a :code:`TealType.bytes` value from a :code:`TealType.uint64` value :code:`n`
 * :code:`Btoi(b)`: generate a :code:`TealType.uint64` value from a :code:`TealType.bytes` value :code:`b`
