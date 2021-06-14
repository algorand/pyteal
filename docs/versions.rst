.. _versions:

TEAL Versions
=============

Each version of PyTeal compiles contracts for a specific version of TEAL. Newer versions of TEAL
introduce new opcodes and transaction fields, so PyTeal must be updated to support these new
features. Below is a table which shows the relationship between TEAL and PyTeal versions.

============ ==============
TEAL Version PyTeal Version
============ ==============
1            <= 0.5.4
2            >= 0.6.0
3            >= 0.7.0
4            >= 0.8.0
============ ==============

In order to support TEAL v2, PyTeal v0.6.0 breaks backward compatibility with v0.5.4. PyTeal
programs written for PyTeal version 0.5.4 and below will not compile properly and most likely will
display an error of the form :code:`AttributeError: * object has no attribute 'teal'`.

**WARNING:** before updating PyTeal to a version with generates TEAL v2 contracts and fixing the
programs to use the global function :any:`compileTeal` rather the class method :code:`.teal()`, make
sure your program abides by the TEAL safety guidelines `<https://developer.algorand.org/docs/reference/teal/guidelines/>`_.
Changing a v1 TEAL program to a v2 TEAL program without any code changes is insecure because v2
TEAL programs allow rekeying. Specifically, you must add a check that the :code:`RekeyTo` property
of any transaction is set to the zero address when updating an older PyTeal program from v0.5.4 and
below.
