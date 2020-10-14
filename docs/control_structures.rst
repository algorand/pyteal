.. _control_flow:

Control Flow
============

PyTeal provides several control flow expressions to chain together multiple expressions and to
conditionally evaluate expressions.

.. _return_expr:

Exiting the Program: :code:`Return`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :any:`Return` expression causes the program to exit immediately. It takes a single argument,
which is the success value that the program should have. For example, :code:`Return(Int(0))` causes
the program to immediately fail, and :code:`Return(Int(1))` causes the program to immediately
succeed. Since the presence of a :code:`Return` statement causes the program to exit, no operations
after it will be executed.

.. _seq_expr:

Chaining Expressions: :code:`Seq`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :any:`Seq` expression can be used to create a sequence of multiple expressions. It takes a
single argument, which is a list of expressions to include in the sequence. For example:

.. code-block:: python

    Seq([
        App.globalPut(Bytes("creator"), Txn.sender()),
        Return(Int(1))
    ])

A :code:`Seq` expression will take on the value of its last expression. Additionally, all
expressions in a :code:`Seq` expression, except the last one, must not return anything (e.g.
evaluate to :any:`TealType.none`). This restriction is in place because intermediate values must not
add things to the TEAL stack. As a result, the following is an invalid sequence:

.. code-block:: python
    :caption: Invalid Seq expression

    Seq([
        Txn.sender(),
        Return(Int(1))
    ])


If you must include an operation that returns a value in the earlier
part of a sequence, you can wrap the value in a :any:`Pop` expression to discard it. For example,

.. code-block:: python

    Seq([
        Pop(Txn.sender()),
        Return(Int(1))
    ])

.. _if_expr:

Simple Branching: :code:`If`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In an :any:`If` expression,

.. code-block:: racket

    If(test-expr, then-expr, else-expr)

the :code:`test-expr` is always evaludated and needs to be typed :code:`TealType.uint64`.
If it results in a value greater than `0`, then the :code:`then-expr` is evaluated.
Otherwise, :code:`else-expr` is evaluated. Note that :code:`then-expr` and :code:`else-expr` must
evaluate to the same type (e.g. both :code:`TealType.uint64`).

You may also invoke an :any:`If` expression without an :code:`else-expr`:

.. code-block:: racket

    If(test-expr, then-expr)

In this case, :code:`then-expr` must be typed :code:`TealType.none`.

.. _assert_expr:

Checking Conditions: :code:`Assert`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :any:`Assert` expression can be used to ensure that conditions are met before continuing the
program. The syntax for :code:`Assert` is:

.. code-block:: racket

    Assert(test-expr)

If :code:`test-expr` is always evaluated and must be typed :code:`TealType.uint64`. If
:code:`test-expr` results in a value greater than `0`, the program continues. Otherwise, the program
immediately exits and indicates that it encountered an error.

Example:

.. code-block:: python

        Assert(Txn.type_enum() == TxnType.Payment)

The above example will cause the program to immediately fail with an error if the transaction type
is not a payment.

.. _cond_expr:

Chaining Tests: :code:`Cond`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A :any:`Cond` expression chians a series of tests to select a result expression.
The syntax of `Cond` is:

.. code-block:: racket

    Cond([test-expr-1, body-1],
         [test-expr-2, body-2],
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


