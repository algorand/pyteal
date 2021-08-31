.. _loading_group_transaction:

Loading Values from Group Transactions
======================================

Since TEAL version 4 and above, programs can load values from transactions within an atomic 
group transaction. For instance, you can import values from the scratch space of another 
application call, and you can access the generated ID of a new application or asset.
These operations are only permitted in application mode.

Accessing IDs of New Apps and Assets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The generated ID of an asset or application from a creation transaction in the current atomic group
can be accessed using the :code:`GeneratedID` expression. The specified transaction index 
may be a Python int or a PyTeal expression that must be evaluated to a uint64 at runtime. 
The transaction index must be less than the index of the current transaction and the 
maximum allowed group size (16).

For example:

.. code-block:: python

    GeneratedID(0) # retrieves the ID from the 0th transaction in current group
    GeneratedID(Int(10)) # retrieves the ID from the 10th transaction in group

Note that if the index is a Python int, it is interpreted as an immediate value (uint8) 
and will be translated to a TEAL :code:`gaid` op. Otherwise, it will be translated 
to a TEAL :code:`gaids` op.

Loading Scratch Slots
~~~~~~~~~~~~~~~~~~~~~

The scratch value from another transaction in the current atomic group can be accessed
using the :code:`ImportScratchValue` expression. The transaction index may be a Python int 
or a PyTeal expression that must be evaluated to a uint64 at runtime, and the scratch slot
ID to load from must be a Python int. 
The transaction index must be less than the index of the current transaction and the 
maximum allowed group size (16), and the slot ID must be less than the maximum number of
scratch slots (256). 

For example, assume an atomic transaction group contains app calls to the following applications,
where App A is called from the first transaction (index 0) and App B is called from the second 
or later transaction. Then the greeting value will be successfully passed between the two contracts.

App A:

.. code-block:: python

    # App is called at transaction index 0
    greeting = ScratchVar(TealType.bytes, 20) # this variable will live in scratch slot 20
    program = Seq([
        If(Txn.sender() == App.globalGet(Bytes("creator")))
        .Then(greeting.store(Bytes("hi creator!")))
        .Else(greeting.store(Bytes("hi user!"))),
        Return(Int(1))
    ])

App B:

.. code-block:: python

    greetingFromPreviousApp = ImportScratchValue(0, 20) # loading scratch slot 20 from the transaction at index 0
    program = Seq([
        # not shown: make sure that the transaction at index 0 is an app call to App A
        App.globalPut(Bytes("greeting from prev app"), greetingFromPreviousApp),
        Return(Int(1))
    ]) 

Note that if the index is a Python int, it is interpreted as an immediate value (uint8) 
and will be translated to a TEAL :code:`gload` op. Otherwise, it will be translated 
to a TEAL :code:`gloads` op.
