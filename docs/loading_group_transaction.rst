.. _loading_group_transaction:

Loading Values from Group Transactions
======================================

Since TEAL version 4 and above, programs can load values from transactions within an atomic 
group transaction. For instance, you can access the ID or scratch slot of another contract 
that is being created within an atomic group of transactions. These operations are only 
permitted in application mode.

Accessing IDs
~~~~~~~~~~~~~

The ID of an asset or application from another transaction in the current atomic group
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

For example:

.. code-block:: python

    ImportScratchValue(0, 1) # retrieves the 1st scratch slot from the 0th transaction in group
    ImportScratchValue(Int(5), 255) # retrieves the 255th scratch slot from the 5th transaction in group

Note that if the index is a Python int, it is interpreted as an immediate value (uint8) 
and will be translated to a TEAL :code:`gload` op. Otherwise, it will be translated 
to a TEAL :code:`gloads` op.
