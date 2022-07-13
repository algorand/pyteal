.. _versions:

AVM Versions
=============

Each version of PyTeal compiles contracts for a specific version of AVM. Newer versions of the AVM
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
============ ==============

In order to support AVM v2, PyTeal v0.6.0 breaks backward compatibility with v0.5.4. PyTeal
programs written for PyTeal version 0.5.4 and below will not compile properly and most likely will
display an error of the form :code:`AttributeError: * object has no attribute 'teal'`.

**WARNING:** before updating PyTeal to a version with generates AVM v2 contracts and fixing the
programs to use the global function :any:`compileTeal` rather the class method :code:`.teal()`, make
sure your program abides by the AVM safety guidelines `<https://developer.algorand.org/docs/reference/teal/guidelines/>`_.
Changing a v1 AVM program to a v2 AVM program without any code changes is insecure because v2
AVM programs allow rekeying. Specifically, you must add a check that the :code:`RekeyTo` property
of any transaction is set to the zero address when updating an older PyTeal program from v0.5.4 and
below.
