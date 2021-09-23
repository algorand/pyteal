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

Byte slices can be extracted from other byte slices using the :any:`Substring` and :any:`Extract`
expressions. These expressions are extremely similar, except one specifies a substring by start and
end indexes, while the other uses a start index and length. Use whichever makes sense for your
application.

Substring
~~~~~~~~~

The :any:`Substring` expression can extract part of a byte slice given start and end indices. For
example:

.. code-block:: python

    Substring(Bytes("algorand"), Int(2), Int(8)) # will produce "gorand"

Extract
~~~~~~~

.. note::
    :code:`Extract` is only available in TEAL version 5 or higher.

The :any:`Extract` expression can extract part of a byte slice given the start index and length. For
example:

.. code-block:: python

    Extract(Bytes("algorand"), Int(2), Int(6)) # will produce "gorand"

Manipulating Individual Bits and Bytes
--------------------------------------

The individual bits and bytes in a byte string can be extracted and changed. See :ref:`bit_and_byte_manipulation`
for more information.
