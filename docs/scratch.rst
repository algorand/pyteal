.. _scratch:

Scratch Operations
========================

Algorand Smart Contracts provides a Scratch Space as a way of temporarily storing values for later use in your code.
You can store up 32 separate values in Scratch Space, each value is stored in separate place called slot.

Writing and Reading
~~~~~~~~~~~~~~~~~~~~~~

To write to Scratch Space, use the :any:`ScratchVar` class. Object of that class represents single slot in the Scratch Space.

To write or read from it you need to use corresponding :any:`ScratchVar.store` or :any:`ScratchVar.load` methods.

Example:

.. code-block:: python

    myvar = ScratchVar(TealType.uint64)
    program = Seq([
        myvar.store(Int(5)),
        Assert(myvar.load() == Int(5))
    ])
