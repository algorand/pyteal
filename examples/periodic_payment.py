#!/usr/bin/env python3

from pyteal import *
import uuid, params, base64
from algosdk import algod, transaction, account, mnemonic

#-------------- using PyTeal program smart contract logic ----------------

#template variables
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

periodic_pay_escrow = And(periodic_pay_core,
                          Or(periodic_pay_transfer, periodic_pay_close))

teal_source = periodic_pay_escrow.teal() 
print("Teal Code:")
print(teal_source)

#--------- compile & send transaction using Goal and Python SDK ----------

# compile teal
teal_file = str(uuid.uuid4()) + ".teal"
with open(teal_file, "w+") as f:
    f.write(teal_source)
lsig_fname = str(uuid.uuid4()) + ".tealc"

stdout, stderr = execute(["goal", "clerk", "compile", "-o", lsig_fname,
                          teal_file])

if stderr != "":
    print(stderr)
    raise
elif len(stdout) < 59:
    print("error in compile teal")
    raise

with open(lsig_fname, "rb") as f:
    teal_bytes = f.read()
lsig = transaction.LogicSig(teal_bytes)

# create algod clients
acl = algod.AlgodClient(params.algod_token, params.algod_address)

#Recover the account that is wanting to delegate signature
passphrase = "patrol crawl rule faculty enemy sick reveal embody trumpet win shy zero ill draw swim excuse tongue under exact baby moral kite spring absent double"
sk = mnemonic.to_private_key(passphrase)
addr = account.address_from_private_key(sk)
print( "Address of Sender/Delgator: " + addr )

# sign the logic signature with an account sk
lsig.sign(sk)

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
startRound = params.lastRound - (params.lastRound % 50)
endRound = startRound + 1000
fee = 0
amount = 2000
receiver = "ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM"

# create a transaction
txn = transaction.PaymentTxn(addr, fee, startRound, endRound, gh, receiver, amount)

# Create the LogicSigTransaction with contract account LogicSig
lstx = transaction.LogicSigTransaction(txn, lsig)

# send raw LogicSigTransaction to network
txid = acl.send_transaction(lstx)
print("Transaction ID: " + txid)


