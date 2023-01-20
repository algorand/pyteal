.. _versions:

Versions
=============

Each version of PyTeal compiles contracts for a specific AVM version. Newer versions of the AVM
introduce new opcodes and transaction fields, so PyTeal must be updated to support these new
features. Below is a table which shows the relationship between AVM and PyTeal versions.

============ ==============
AVM Version  PyTeal Version
============ ==============
1            <= 0.5.4
2            >= 0.6.0
3            >= 0.7.0
4            >= 0.8.0
5            >= 0.9.0
6            >= 0.10.0
7            >= 0.15.0
8            >= 0.20.0
============ ==============

.. _version pragmas:

Version Pragmas
----------------

When writing a PyTeal smart contract, it's important to target a specific AVM version and to compile
with a single PyTeal version. This will ensure your compiled program remains consistent and has the
exact same behavior no matter when you compile it.

The :any:`pragma` function can be used to assert that the current PyTeal version matches a constraint
of your choosing. This can help strengthen the dependency your source code has on the PyTeal package
version you used when writing it.

If you are writing code for others to consume, or if your codebase has different PyTeal version
dependencies in different places, the :any:`Pragma` expression can be used to apply a pragma
constraint to only a section of the AST.

PyTeal v0.5.4 and Below
-----------------------

In order to support AVM v2, PyTeal v0.6.0 breaks backward compatibility with v0.5.4. PyTeal
programs written for PyTeal version 0.5.4 and below will not compile properly and most likely will
display an error of the form :code:`AttributeError: * object has no attribute 'teal'`.

.. warning::
    If you are updating from a v1 AVM program, make
    sure your program abides by the `TEAL safety guidelines <https://developer.algorand.org/docs/reference/teal/guidelines/>`_.
    Changing a v1 AVM program to a v2 AVM program without any code changes is insecure because v2
    AVM programs allow rekeying. Specifically, you must add a check that the :code:`RekeyTo` property
    of any transaction is set to the zero address when updating an older PyTeal program from v0.5.4 and
    below.
