.. _control_flow:

Control Flow
============

PyTeal provides several control flow expressions to create programs.

.. _return_expr:

Exiting the Program: :code:`Approve` and :code:`Reject`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    The :code:`Approve` and :code:`Reject` expressions are only available in TEAL version 4 or higher.
    Prior to this, :code:`Return(Int(1))` is equivalent to :code:`Approve()` and :code:`Return(Int(0))`
    is equivalent to :code:`Reject()`.

The :any:`Approve` and :any:`Reject` expressions cause the program to immediately exit. If :code:`Approve`
is used, then the execution is marked as successful, and if :code:`Reject` is used, then the execution
is marked as unsuccessful.

These expressions also work inside :ref:`subroutines <subroutine_expr>`.

.. _seq_expr:

Chaining Expressions: :code:`Seq`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :any:`Seq` expression can be used to create a sequence of multiple expressions.  It's arguments are the 
expressions to include in the sequence, either as a variable number of arguments, or as a single list

For example:

.. code-block:: python

    Seq(
        App.globalPut(Bytes("creator"), Txn.sender()),
        Return(Int(1))
    )

A :code:`Seq` expression will take on the value of its last expression. Additionally, all
expressions in a :code:`Seq` expression, except the last one, must not return anything (e.g.
evaluate to :any:`TealType.none`). This restriction is in place because intermediate values must not
add things to the TEAL stack. As a result, the following is an invalid sequence:

.. code-block:: python
    :caption: Invalid Seq expression

    Seq(
        Txn.sender(),
        Return(Int(1))
    )


If you must include an operation that returns a value in the earlier
part of a sequence, you can wrap the value in a :any:`Pop` expression to discard it. For example,

.. code-block:: python

    Seq(
        Pop(Txn.sender()),
        Return(Int(1))
    )

.. _if_expr:

Simple Branching: :code:`If`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In an :any:`If` expression,

.. code-block:: racket

    If(test-expr, then-expr, else-expr)

the :code:`test-expr` is always evaluated and needs to be typed :code:`TealType.uint64`.
If it results in a value greater than `0`, then the :code:`then-expr` is evaluated.
Otherwise, :code:`else-expr` is evaluated. Note that :code:`then-expr` and :code:`else-expr` must
evaluate to the same type (e.g. both :code:`TealType.uint64`).

You may also invoke an :any:`If` expression without an :code:`else-expr`:

.. code-block:: racket

    If(test-expr, then-expr)

In this case, :code:`then-expr` must be typed :code:`TealType.none`.

There is also an alternate way to write an :any:`If` expression that makes reading
complex statements easier to read.

.. code-block:: racket

    If(test-expr)
    .Then(then-expr)
    .ElseIf(test-expr)
    .Then(then-expr)
    .Else(else-expr)

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

A :any:`Cond` expression chains a series of tests to select a result expression.
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

.. _loop_while_expr:

Looping: :code:`While`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    This expression is only available in TEAL version 4 or higher.

The :any:`While` expression can be used to create simple loops in PyTeal. The syntax of :code:`While` is:

.. code-block:: racket

    While(loop-condition).Do(loop-body)

The :code:`loop-condition` expression must evaluate to :code:`TealType.uint64`, and the :code:`loop-body`
expression must evaluate to :code:`TealType.none`.

The :code:`loop-body` expression will continue to execute as long as :code:`loop-condition` produces
a true value (`> 0`).

For example, the following code uses :any:`ScratchVar` to iterate through every transaction in the
current group and sum up all of their fees.

.. code-block:: python

        totalFees = ScratchVar(TealType.uint64)
        i = ScratchVar(TealType.uint64)

        Seq([
            i.store(Int(0)),
            totalFees.store(Int(0)),
            While(i.load() < Global.group_size()).Do(Seq([
                totalFees.store(totalFees.load() + Gtxn[i.load()].fee()),
                i.store(i.load() + Int(1))
            ]))
        ])

.. _loop_for_expr:

Looping: :code:`For`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    This expression is only available in TEAL version 4 or higher.

Similar to :code:`While`, the :any:`For` expression can also be used to create loops in PyTeal. The
syntax of :code:`For` is:

.. code-block:: racket

    For(loop-start, loop-condition, loop-step).Do(loop-body)

The :code:`loop-start`, :code:`loop-step`, and :code:`loop-body` expressions must evaluate to
:code:`TealType.none`, and the the :code:`loop-condition` expression must evaluate to :code:`TealType.uint64`.

When a :code:`For` expression is executed, :code:`loop-start` is executed first. Then the
expressions :code:`loop-condition`, :code:`loop-body`, and :code:`loop-step` will continue to
execute in order as long as :code:`loop-condition` produces a true value (`> 0`).

For example, the following code uses :any:`ScratchVar` to iterate through every transaction in the
current group and sum up all of their fees. The code here is functionally equivalent to the
:code:`While` loop example above.

.. code-block:: python

        totalFees = ScratchVar(TealType.uint64)
        i = ScratchVar(TealType.uint64)

        Seq([
            totalFees.store(Int(0)),
            For(i.store(Int(0)), i.load() < Global.group_size(), i.store(i.load() + Int(1))).Do(
                totalFees.store(totalFees.load() + Gtxn[i.load()].fee())
            )
        ])

.. _loop_exit_expr:

Exiting Loops: :code:`Continue` and :code:`Break`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The expressions :any:`Continue` and :any:`Break` can be used to exit :code:`While` and :code:`For`
loops in different ways.

When :code:`Continue` is present in the loop body, it instructs the program to skip the remainder
of the loop body. The loop may continue to execute as long as its condition remains true.

For example, the code below iterates though every transaction in the current group and counts how
many are payments, using the :code:`Continue` expression.

.. code-block:: python

        numPayments = ScratchVar(TealType.uint64)
        i = ScratchVar(TealType.uint64)

        Seq([
            numPayments.store(Int(0)),
            For(i.store(Int(0)), i.load() < Global.group_size(), i.store(i.load() + Int(1))).Do(Seq([
                If(Gtxn[i.load()].type_enum() != TxnType.Payment)
                .Then(Continue()),
                numPayments.store(numPayments.load() + Int(1))
            ]))
        ])

When :code:`Break` is present in the loop body, it instructs the program to completely exit the
current loop. The loop will not continue to execute, even if its condition remains true.

For example, the code below finds the index of the first payment transaction in the current group,
using the :code:`Break` expression.

.. code-block:: python

        firstPaymentIndex = ScratchVar(TealType.uint64)
        i = ScratchVar(TealType.uint64)

        Seq([
            # store a default value in case no payment transactions are found
            firstPaymentIndex.store(Global.group_size()),
            For(i.store(Int(0)), i.load() < Global.group_size(), i.store(i.load() + Int(1))).Do(
                If(Gtxn[i.load()].type_enum() == TxnType.Payment)
                .Then(Seq([
                    firstPaymentIndex.store(i.load()),
                    Break()
                ]))
            ),
            # assert that a payment was found
            Assert(firstPaymentIndex.load() < Global.group_size())
        ])

.. _subroutine_expr:

Subroutines
~~~~~~~~~~~

.. note::
    Subroutines are only available in TEAL version 4 or higher.

A subroutine is section of code that can be called multiple times from within a program. Subroutines
are PyTeal's equivalent to functions. Subroutines can accept any number of arguments, and these
arguments must be PyTeal expressions. Additionally, a subroutine may return a single value, or no value.

Creating Subroutines
--------------------

To create a subroutine, apply the :any:`Subroutine` function decorator to a Python function which
implements the subroutine. This decorator takes one argument, which is the return type of the subroutine.
:any:`TealType.none` indicates that the subroutine does not return a value, and any other type
(e.g. :any:`TealType.uint64` or :any:`TealType.bytes`) indicates the return type of the single value
the subroutine returns.

For example,

.. code-block:: python

        @Subroutine(TealType.uint64)
        def isEven(i):
            return i % Int(2) == Int(0)

Calling Subroutines
-------------------

To call a subroutine, simply call it like a normal Python function and pass in its arguments. For example,

.. code-block:: python

        App.globalPut(Bytes("value_is_even"), isEven(Int(10)))

Recursion
---------

Recursion with subroutines is also possible. For example, the subroutine below also checks if its
argument is even, but uses recursion to do so.

.. code-block:: python

        @Subroutine(TealType.uint64)
        def recursiveIsEven(i):
            return (
                If(i == Int(0))
                .Then(Int(1))
                .ElseIf(i == Int(1))
                .Then(Int(0))
                .Else(recursiveIsEven(i - Int(2)))
            )

Exiting Subroutines
-------------------

The :any:`Return` expression can be used to explicitly return from a subroutine.

If the subroutine does not return a value, :code:`Return` should be called with no arguments. For
example, the subroutine below asserts that the first payment transaction in the current group has a
fee of 0:

.. code-block:: python

        @Subroutine(TealType.none)
        def assertFirstPaymentHasZeroFee():
            i = ScratchVar(TealType.uint64)

            return Seq([
                For(i.store(Int(0)), i.load() < Global.group_size(), i.store(i.load() + Int(1))).Do(
                    If(Gtxn[i.load()].type_enum() == TxnType.Payment)
                    .Then(Seq([
                        Assert(Gtxn[i.load()].fee() == Int(0)),
                        Return()
                    ]))
                ),
                # no payments found
                Err()
            ])

Otherwise if the subroutine does return a value, that value should be the argument to the :code:`Return`
expression. For example, the subroutine below checks whether the current group contains a payment
transaction:

.. code-block:: python

        @Subroutine(TealType.uint64)
        def hasPayment():
            i = ScratchVar(TealType.uint64)

            return Seq([
                For(i.store(Int(0)), i.load() < Global.group_size(), i.store(i.load() + Int(1))).Do(
                    If(Gtxn[i.load()].type_enum() == TxnType.Payment)
                    .Then(Return(Int(1)))
                ),
                Return(Int(0))
            ])

:code:`Return` can also be called from the main program. In this case, a single integer argument
should be provided, which is the success value for the current execution. A true value (`> 0`)
is equivalent to :any:`Approve`, and a false value is equivalent to :any:`Reject`.
