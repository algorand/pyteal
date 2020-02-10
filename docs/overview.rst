Overview
========

With PyTeal, developers can easily write `Algorand Smart Contracts (ASC1s) <https://developer.algorand.org/docs/asc>`_ in Python.

Below is the example of writing *Hashed Time Locked Contract* in Pyteal::

  from pyteal import *

  """ Hash Time Locked Contract
  """
  alice = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
  bob = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
  secret = Bytes("base32", "23232323232323")

  fee_cond = Txn.fee() < Int(1000)
  
  type_cond = Txn.type_enum() == Int(1)
  
  recv_cond = And(Txn.close_remainder_to() == Global.zero_address(),
                  Txn.receiver() == alice,
                  Sha256(Arg(0)) == secret)
		  
  esc_cond = And(Txn.close_remainder_to()  == Global.zero_address(),
                 Txn.receiver() == bob,
                 Txn.first_valid() > Int(3000))

  atomic_swap = And(fee_cond,
                    type_cond,
		    Or(recv_cond, esc_cond))

  print(atomic_swap.teal())


As shown in this exmaple, the logic of smart contract is expressed using PyTeal expressions constructed in Python. PyTeal overloads Python's arithmetic operators 
such as :code:`<` and :code:`==` (more overloaded operators can be found in :ref:`arithmetic_expressions`), allowing Python developers express smart contract logic more naturally.

Last, :code:`teal()` is called to convert an PyTeal expression
to a TEAL program, consisting a sequence of TEAL opcodes.
The output of the above example is: ::

  txn Fee
  int 1000
  <
  txn TypeEnum
  int 1
  ==
  &&
  txn CloseRemainderTo
  global ZeroAddress
  ==
  txn Receiver
  addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
  ==
  &&
  arg 0
  sha256
  byte base32 23232323232323
  ==
  &&
  txn CloseRemainderTo
  global ZeroAddress
  ==
  txn Receiver
  addr 7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M
  ==
  &&
  txn FirstValid
  int 3000
  >
  &&
  ||
  &&

