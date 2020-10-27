Overview
========

With PyTeal, developers can easily write `Algorand Smart Contracts (ASC1s) <https://developer.algorand.org/docs/features/asc1/>`_ in Python.
PyTeal supports both stateless and statefull smart contracts.

Below is an example of writing a basic stateless smart contract that allows a specific receiver to withdraw funds from an account.

.. literalinclude:: ../examples/signature/basic.py
    :language: python

As shown in this exmaple, the logic of smart contract is expressed using PyTeal expressions constructed in Python. PyTeal overloads Python's arithmetic operators 
such as :code:`<` and :code:`==` (more overloaded operators can be found in :ref:`arithmetic_expressions`), allowing Python developers express smart contract logic more naturally.

Lastly, :any:`compileTeal` is called to convert an PyTeal expression
to a TEAL program, consisting of a sequence of TEAL opcodes.
The output of the above example is:

.. literalinclude:: ../examples/signature/basic.teal
