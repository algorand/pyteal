.. _byte_expressions:

Byte Operators
====================

TEAL byte slices are similar to strings and can be manipulated in the same way.

Length
------

The length of a byte slice can be obtained using the :any:`Len` expression. For example:

.. code-block:: python

    Len(Bytes("")) # will produce 0
    Len(Bytes("algorand")) # will produce 8

Concatenation
-------------

Byte slices can be combined using the :any:`Concat` expression. This expression takes at least
two arguments and produces a new byte slice consisting of each argument, one after another. For
example:

.. code-block:: python

    Concat(Bytes("a"), Bytes("b"), Bytes("c")) # will produce "abc"

Substring Extraction
--------------------

Byte slices can be extracted from other byte slices using the :any:`Substring` expression. This
expression can extract part of a byte slicing given start and end indices. For example:

.. code-block:: python

    Substring(Bytes("algorand"), Int(0), Int(4)) # will produce "algo"

Manipulating Individual Bits and Bytes
--------------------------------------

The individual bits and bytes in a byte string can be extracted and changed. See :ref:`bit_and_byte_manipulation`
for more information.
