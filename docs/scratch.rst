.. _scratch:

Scratch Space
========================

`Scratch space <https://developer.algorand.org/docs/reference/teal/specification/#scratch-space>`_
is a temporary place to store values for later use in your program. It is temporary because any
changes to scratch space do not persist beyond the current transaction. Scratch space can be used
in both Application and Signature mode.

Scratch space consists of 256 scratch slots, each capable of storing one integer or byte slice. When
using the :any:`ScratchVar` class to work with scratch space, a slot is automatically assigned to
each variable.

ScratchVar:  Writing and Reading to/from Scratch Space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To write to scratch space, first create a :any:`ScratchVar` object and pass in the :any:`TealType`
of the values that you will store there. It is possible to create a :any:`ScratchVar` that can store
both integers and byte slices by passing no arguments to the :any:`ScratchVar` constructor, but note
that no type checking takes places in this situation. It is also possible to manually specify which 
slot ID the compiler should assign the scratch slot to in the TEAL code. If no slot ID is specified,
the compiler will assign it to any available slot. 

To write or read values, use the corresponding :any:`ScratchVar.store` or :any:`ScratchVar.load` methods.  :any:`ScratchVar.store` *must* be invoked before invoking :any:`ScratchVar.load`.

For example:

.. code-block:: python

    myvar = ScratchVar(TealType.uint64) # assign a scratch slot in any available slot
    program = Seq([
        myvar.store(Int(5)),
        Assert(myvar.load() == Int(5))
    ])
    anotherVar = ScratchVar(TealType.bytes, 4) # assign this scratch slot to slot #4

DynamicScratchVar:  Referencing a ScratchVar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:any:`DynamicScratchVar` functions as a pointer to a :any:`ScratchVar` instance.

Reference a :any:`ScratchVar` instance by invoking :any:`DynamicScratchVar.set_index`.  :any:`DynamicScratchVar.set_index` *must* be invoked before using :any:`DynamicScratchVar.load` and :any:`DynamicScratchVar.store`.

Here's an example to motivate usage.  The example shows how a :any:`DynamicScratchVar` updates the *value* of a referenced :any:`ScratchVar` from 7 to 10.

.. code-block:: python

    s = ScratchVar(TealType.uint64)
    d = DynamicScratchVar(TealType.uint64)

    return Seq(
        d.set_index(s),
        s.store(Int(7)),
        d.store(d.load() + Int(3)),
        Assert(s.load() == Int(10)),
        Int(1),
    )
