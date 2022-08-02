.. _api:

PyTeal Package
==============

.. automodule:: pyteal
   :members:
   :undoc-members:
   :imported-members:
   :special-members: __getitem__
   :show-inheritance:

   .. data:: Txn
      :annotation: = <pyteal.TxnObject object>

      The current transaction being evaluated. This is an instance of :any:`TxnObject`.

   .. data:: Gtxn
      :annotation: = <pyteal.TxnGroup object>

      The current group of transactions being evaluated. This is an instance of :any:`TxnGroup`.

   .. data:: InnerTxn
      :annotation: = <pyteal.TxnObject object>

      The most recently submitted inner transaction. This is an instance of :any:`TxnObject`.

      If a transaction group was submitted most recently, then this will be the last transaction in that group.

   .. data:: Gitxn
      :annotation: = <pyteal.InnerTxnGroup object>

      The most recently submitted inner transaction group. This is an instance of :any:`InnerTxnGroup`.

      If a single transaction was submitted most recently, then this will be a group of size 1.

.. automodule:: pyteal.abi
   :members:
   :undoc-members:
   :imported-members:
   :special-members: __getitem__
   :show-inheritance:
