.. _conditionals:

Conditionals
============

PyTeal provides two conditional expressions, the simple branching
:code:`If` expression, and :code:`Cond` expression for chaining tests.

.. _if_expr:

Simple Branching: :code:`If`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In an :code:`If` expression,

.. code-block:: racket

	If(test-expr, then-expr, else-expr)

the :code:`test-expr` is always evaludated and needs to be typed :code:`TealType.uint64`.
If it results in a value greater than `0`, then the :code:`then-expr` is evaluated.
Otherwise, :code:`else-expr` is evaluated.

An :code:`If` expression must contain a :code:`then-expr` and an :code:`else-expr`; the
later is not optional.

.. _cond_expr:

Chaining Tests: :code:`Cond`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A code:`Cond` expression chians a series of tests to select a result expression.
The syntax of `Cond` is:

.. code-block:: racket

	Cond([test-expr body],
	     . . . )

Each :code:`test-expr` is evaluated in order. If it produces `0`, the paired :code:`body`
is ignored, and evaluation proceeds to the next :code:`test-expr`.
As soon as a :code:`test-expr` produces a true value (`> 0`),
its :code:`body` is evaluated to produce the value for this :code:`Cond` expression.
If none of :code:`test-expr` s evaluates to a true value, the :code:`Cond` expression will
be evaluated to :code:`err`, a TEAL opcode that causes the runtime panic.

In a :code:`Cond` expression, each :code:`test-expr` needs to be typed :code:`TealType.uint64`.
A :code:`body` could be typed either :code:`TealType.uint64` or :code:`TealType.bytes`. However, all
:code:`body` s must have the same data type. Otherwise, a :code:`TealTypeError` is triggered.

Example:



.. code-block:: python

        Cond([Global.group_size() == Int(5), bid],
             [Global.group_size() == Int(4), redeem],
             [Global.group_size() == Int(1), wrapup])


This PyTeal code branches on the size of the atomic transaction group.


