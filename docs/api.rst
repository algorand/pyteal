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
