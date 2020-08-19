.. _examples:

PyTeal Examples
===============

Here are some additional PyTeal example programs:

Signature Mode
--------------

Atomic Swap
~~~~~~~~~~~~~~~

*Atomic Swap* allows the transfer of Algos from a buyer to a seller in exchange for a good or
service. This is done using a *Hashed Time Locked Contract*. In this scheme, the buyer and funds a
TEAL account with the sale price. The buyer also picks a secret value and encodes a secure hash of
this value in the TEAL program. The TEAL program will transfer its balance to the seller if the
seller is able to provide the secret value that corresponds to the hash in the program. When the
seller renders the good or service to the buyer, the buyer discloses the secret from the program.
The seller can immediately verify the secret and withdraw the payment.

.. literalinclude:: ../examples/atomic_swap.py
    :language: python

Split Payment
~~~~~~~~~~~~~

*Split Payment* splits payment between :code:`tmpl_rcv1` and :code:`tmpl_rcv2` on the ratio of
:code:`tmpl_ratn / tmpl_ratd`.

.. literalinclude:: ../examples/split.py
    :language: python

Periodic Payment
~~~~~~~~~~~~~~~~

*Periodic Payment* allows some account to execute periodic withdrawal of funds. This PyTeal program
creates an contract account that allows :code:`tmpl_rcv` to withdraw :code:`tmpl_amt` every
:code:`tmpl_period` rounds for :code:`tmpl_dur` after every multiple of :code:`tmpl_period`.

After :code:`tmpl_timeout`, all remaining funds in the escrow are available to :code:`tmpl_rcv`.

.. literalinclude:: ../examples/periodic_payment.py
    :language: python

Application Mode
----------------

TODO
