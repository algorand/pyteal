.. _compiler_optimization:

Compiler Optimization
========================
**The optimizer is at an early stage and is disabled by default. Backwards compatability cannot be
guaranteed at this point.**

The optimizer is a tool for improving performance and reducing resource consumption. In this context,
the terms *performance* and *resource* can apply across multiple dimensions, including but not limited
to: compiled code size, scratch slot usage, opcode cost, etc. 

Optimizer Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The compiler determines which optimizations to apply based on the provided :any:`OptimizeOptions` object as
shown in the code block below. The :any:`OptimizeOptions` constructor receives a set of keyword arguments 
representing flags corresponding to particular optimizations. If arguments are not provided to the
constructor or no :any:`OptimizeOptions` object is passed to :any:`compileTeal` then the default behavior is
that no optimizations are applied.

============================== ================================================================================ ===========================
Optimization Flag              Description                                                                      Default
============================== ================================================================================ ===========================
:code:`scratch_slots`          A boolean describing whether or not scratch slot optimization should be applied. :code:`False`
============================== ================================================================================ ===========================

.. code-block:: python

    optimize_options = OptimizeOptions(scratch_slots=True)
    compileTeal(approval_program(), mode=Mode.Application, version=4, optimize=optimize_options)
