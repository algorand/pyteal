.. _examples:

PyTeal Examples
===============

We showcase some example PyTeal programs:


Split Payment
~~~~~~~~~~~~~

*Split Payment* splits payment between :code:`tmpl_rcv1` and
:code:`tmpl_rcv2` on the ratio of :code:`tmpl_ratn / tmpl_ratd` ::

	from pyteal import *

	"""Split
	"""

	# template variables
	tmpl_fee = Int(1000)
	tmpl_rcv1 = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
	tmpl_rcv2 = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
	tmpl_own = Addr("5MK5NGBRT5RL6IGUSYDIX5P7TNNZKRVXKT6FGVI6UVK6IZAWTYQGE4RZIQ")
	tmpl_ratn  = Int(1)
	tmpl_ratd = Int(3)
	tmpl_min_pay = Int(1000)
	tmpl_timeout = Int(3000)
	
	split_core = (Txn.type_enum() == Int(1)).And(Txn.fee() < tmpl_fee)

	split_transfer = And(Gtxn.sender(0) == Gtxn.sender(1),
                             Txn.close_remainder_to() == Global.zero_address(),
                             Gtxn.receiver(0) == tmpl_rcv1,
                             Gtxn.receiver(1) == tmpl_rcv2,
                             Gtxn.amount(0) == ((Gtxn.amount(0) + Gtxn.amount(1)) * tmpl_ratn) / tmpl_ratd,
                             Gtxn.amount(0) == tmpl_min_pay)

	split_close = And(Txn.close_remainder_to() == tmpl_own,
                          Txn.receiver() == Global.zero_address(),
                          Txn.first_valid() == tmpl_timeout)

	split = And(split_core,
                    If(Global.group_size() == Int(2),
                       split_transfer,
                       split_close))

	print(split.teal())


Periodic Payment
~~~~~~~~~~~~~~~~

*Periodic Payment*  allows some account to execute periodic withdrawal of funds. This PyTeal program creates an contract account that allows :code:`tmpl_rcv` to withdraw TMPL_AMT every :code:`tmpl_period` rounds for :code:`tmpl_dur` after every multiple
of :code:`tmpl_period`.

After :code:`tmpl_timeout`, all remaining funds in the escrow
are available to :code:`tmpl_rcv` ::

  from pyteal import *

  tmpl_fee = Int(1000)
  tmpl_period = Int(50)
  tmpl_dur = Int(5000)
  tmpl_x = Bytes("base64", "023sdDE2")
  tmpl_amt = Int(2000)
  tmpl_rcv = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
  tmpl_timeout = Int(30000)

  periodic_pay_core = And(Txn.type_enum() == Int(1),
                         Txn.fee() < tmpl_fee,
                         Txn.first_valid() % tmpl_period == Int(0),
                         Txn.last_valid() == tmpl_dur + Txn.first_valid(),
                         Txn.lease() == tmpl_x)
                      

  periodic_pay_transfer = And(Txn.close_remainder_to() ==  Global.zero_address(),
                              Txn.receiver() == tmpl_rcv,
                              Txn.amount() == tmpl_amt)

  periodic_pay_close = And(Txn.close_remainder_to() == tmpl_rcv,
                           Txn.receiver() == Global.zero_address(),
                           Txn.first_valid() == tmpl_timeout,
                           Txn.amount() == Int(0))

  periodic_pay_escrow = periodic_pay_core.And(periodic_pay_transfer.Or(periodic_pay_close))

  print(periodic_pay_escrow.teal())

