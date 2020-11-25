.. _scratch:

Scratch Space
========================

`Scratch space <https://developer.algorand.org/docs/reference/teal/specification/#scratch-space>`_
is a temporary place to store values for later use in your program. It is temporary because any
changes to scratch space do not persist beyond the current tranasaction. Scratch space can be used
in both Application and Signature mode.

Scratch space consists of 256 scratch slots, each capable of storing one integer or byte slice. When
using the :any:`ScratchVar` class to work with scratch space, a slot is automatically assigned to
each variable.

Writing and Reading
~~~~~~~~~~~~~~~~~~~~~~

To write to scratch space, first create a :any:`ScratchVar` object and pass in the :any:`TealType`
of the values that you will store there. It is possible to create a :any:`ScratchVar` that can store
both integers and byte slices by passing no arguments to the :any:`ScratchVar` constructor, but note
that no type checking takes places in this situation.

To write or read values, use the corresponding :any:`ScratchVar.store` or :any:`ScratchVar.load` methods.

For example:

.. code-block:: python

    myvar = ScratchVar(TealType.uint64)
    program = Seq([
        myvar.store(Int(5)),
        Assert(myvar.load() == Int(5))
    ])
