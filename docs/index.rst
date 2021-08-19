.. PyTeal documentation master file, created by
   sphinx-quickstart on Fri Jan 31 14:27:13 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyTeal: Algorand Smart Contracts in Python
==========================================

PyTeal is a Python language binding for `Algorand Smart Contracts (ASC1s) <https://developer.algorand.org/docs/asc>`_. 

Algorand Smart Contracts are implemented using a new language that is stack-based, 
called `Transaction Execution Approval Language (TEAL) <https://developer.algorand.org/docs/teal>`_. 
This a non-Turing complete language that allows branch forwards but prevents recursive logic 
to maximize safety and performance. 

However, TEAL is essentially an assembly language.
With PyTeal, developers can express smart contract logic purely using Python. 
PyTeal provides high level, functional programming style abstactions over TEAL
and does type checking at construction time.

The :doc:`User Guide </data_type>` describes many useful features in PyTeal, and the complete documentation for every expression and operation can be found in the :doc:`PyTeal Package API documentation </api>`.

PyTeal **hasn't been security audited**. Use it at your own risk.

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   overview
   installation
   examples

.. toctree::
   :maxdepth: 1
   :caption: User Guide

   data_type
   arithmetic_expression
   byte_expression
   accessing_transaction_field
   crypto
   scratch
   loading_group_transaction
   control_structures
   state
   assets
   versions

.. toctree::
   :maxdepth: 3
   :caption: API

   api

Indices and tables
==================

* :ref:`genindex`
