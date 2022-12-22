.. _compiler_optimization:

Compiler Optimization
========================

The optimizer is a tool for improving performance and reducing resource consumption. In this context,
the terms *performance* and *resource* can apply across multiple dimensions, including but not limited
to: compiled code size, scratch slot usage, opcode cost, etc. 

Optimizer Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The compiler determines which optimizations to apply based on the provided :any:`OptimizeOptions` object as
shown in the code block below. Both :any:`compileTeal` as well as the :any:`Router.compile_program` method
can receive an :code:`optimize` parameter of type :any:`OptimizeOptions`.


.. code-block:: python

    # optimize scratch slots for all program versions (shown is version 4)
    optimize_options = OptimizeOptions(scratch_slots=True)
    compileTeal(approval_program(), mode=Mode.Application, version=4, optimize=optimize_options)

============================== ================================================================================ ===========================
Optimization Flag              Description                                                                      Default
============================== ================================================================================ ===========================
:code:`scratch_slots`          A boolean describing whether or not scratch slot optimization should be applied. :code:`False`
============================== ================================================================================ ===========================

Default Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :any:`OptimizeOptions` constructor receives keyword arguments representing flags for particular optimizations.
If an argument is not provided to the constructor of :any:`OptimizeOptions`, a default program version dependent 
optimization behavior is used in its place according to the table below. 


.. list-table::
   :widths: 25 25 25 25 25
   :header-rows: 1

   * - Optimization Flag
     - Value
     - Interpretation
     - Program Version
     - Behavior
   * - :code:`scratch_slots`
     - :code:`None`
     - Default
     - ≥ 9
     - Scratch slot optimization is applied
   * -
     - :code:`None`
     - Default
     - ≤ 8
     - Scratch slot optimization is *not* applied
   * -
     - :code:`True`
     - Enable
     - *any*
     - Scratch slot optimization is applied
   * -
     - :code:`False`
     - Disable
     - *any*
     - Scratch slot optimization is *not* applied
   * - :code:`frame_pointers`
     - :code:`None`
     - Default
     - ≥ 8
     - Frame pointers available and are therefore applied
   * -
     - :code:`None`
     - Default
     - ≤ 7
     - Frame pointers not available and not applied
   * -
     - :code:`True`
     - Enable
     - ≥ 8
     - Frame pointers available and applied
   * -
     - :code:`True`
     - *attempt*
     - ≤ 7
     - An error occurs when attempting to compile as frame pointers are not available
   * -
     - :code:`False`
     - Disable
     - *any*
     - Frame pointers not applied
   

When the :code:`optimize` parameter is omitted in :any:`compileTeal` 
or :any:`Router.compile_program`, all parameters conform to program version dependent defaults
as defined in the above table. For example:

.. code-block:: python

    # apply default optimization behavior by NOT providing `OptimizeOptions`
    # for version 9 as shown next, this is equivalent to passing in 
    # optimize=OptimizeOptions(scratch_slots=True, frame_pointers=True)

    compileTeal(approval_program(), mode=Mode.Application, version=9)

    # for version 8 as shown next, this is equivalent to passing in 
    # optimize=OptimizeOptions(scratch_slots=False, frame_pointers=True)

    compileTeal(approval_program(), mode=Mode.Application, version=8)
