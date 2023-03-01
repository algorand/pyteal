#!/usr/bin/env python3

import base64
import params
import uuid

from algosdk import account, algod, mnemonic, transaction
from pyteal import *

from recurring_swap import recurring_swap

# Compile TEAL source code
teal_source = compileTeal(recurring_swap(), mode=Mode.Signature, version=2)

# Compile TEAL program with Python SDK
compiled_teal = transaction.compile_teal(teal_source)

# Create an algod client
acl = algod.AlgodClient(params.algod_token, params.algod_address)

# Recover the account that is wanting to delegate signature
passphrase = "patrol crawl rule faculty enemy sick reveal embody trumpet win shy zero ill draw swim excuse tongue under exact baby moral kite spring absent double"
sk = mnemonic.to_private_key(passphrase)
addr = account.address_from_private_key(sk)
print("Dispense at least 201000 microAlgo to {}".format(addr))
input("Make sure you did that. Press Enter to continue...")

# Get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
startRound = params["lastRound"] - (params["lastRound"] % 1000)
endRound = startRound + 1000
fee = 1000
amount = 200000
receiver = "ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM"
lease = base64.b64decode("y9OJ5MRLCHQj8GqbikAUKMBI7hom+SOj8dlopNdNHXI=")

# Create a transaction
txn = transaction.PaymentTxn(addr, fee, startRound, endRound, gh, receiver, amount, flat_fee=True, lease=lease)

# Create a logic signature from compiled TEAL program
lsig = transaction.LogicSig(compiled_teal)

# Sign the logic signature with an account sk
lsig.sign(sk)

# Create a logic signature transaction with the contract account LogicSig
lstx = transaction.LogicSigTransaction(txn, lsig)

# Write the transaction to a file
txns = [lstx]
transaction.write_to_file(txns, "r_swap.stxn")

# Send the raw LogicSigTransaction to the network
txid = acl.send_transaction(lstx)
print("Transaction ID: " + txid)
