.. _byte_expressions:

Byte Operators
====================

TEAL byte slices are similar to strings and can be manipulated in much the same way.

Concat
--------------------

Byte slices can be combined using the :any:`Concat` expression. This expression takes at least
two arguments and produces a new byte slice consisting of each argument, one after another. For
example:

.. code-block:: python

    Concat(Bytes("a"), Bytes("b"), Bytes("c")) # equivalent to Bytes("abc")

Substring
--------------------

Byte slices can be extracted from other byte slices using the :any:`Substring` expression. This
expression can extract part of a byte slicing given start and end indices. For example:

.. code-block:: python

    Substring(Bytes("algorand"), Int(0), Int(4)) # equivalent to Bytes("algo")
