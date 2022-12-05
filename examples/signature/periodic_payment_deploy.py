#!/usr/bin/env python3

import base64
import params
import uuid

from algosdk import algod, transaction, account, mnemonic
from periodic_payment import periodic_payment

from pyteal import *

# --------- compile & send transaction using Goal and Python SDK ----------

teal_source = compileTeal(periodic_payment(), mode=Mode.Signature, version=2)

# compile teal
teal_file = str(uuid.uuid4()) + ".teal"
with open(teal_file, "w+") as f:
    f.write(teal_source)
lsig_fname = str(uuid.uuid4()) + ".tealc"

stdout, stderr = execute(["goal", "clerk", "compile", "-o", lsig_fname, teal_file])

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

# Recover the account that is wanting to delegate signature
passphrase = "patrol crawl rule faculty enemy sick reveal embody trumpet win shy zero ill draw swim excuse tongue under exact baby moral kite spring absent double"
sk = mnemonic.to_private_key(passphrase)
addr = account.address_from_private_key(sk)
print("Dispense at least 201000 microAlgo to {}".format(addr))
input("Make sure you did that. Press Enter to continue...")

# sign the logic signature with an account sk
lsig.sign(sk)

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
startRound = params["lastRound"] - (params["lastRound"] % 1000)
endRound = startRound + 1000
fee = 1000
amount = 200000
receiver = "ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM"
lease = base64.b64decode("y9OJ5MRLCHQj8GqbikAUKMBI7hom+SOj8dlopNdNHXI=")

# create a transaction
txn = transaction.PaymentTxn(
    addr, fee, startRound, endRound, gh, receiver, amount, flat_fee=True, lease=lease
)

# Create the LogicSigTransaction with contract account LogicSig
lstx = transaction.LogicSigTransaction(txn, lsig)

# write to file
txns = [lstx]
transaction.write_to_file(txns, "p_pay.stxn")

# send raw LogicSigTransaction to network
txid = acl.send_transaction(lstx)
print("Transaction ID: " + txid)
# except Exception as e:
#     print(e)

# send raw LogicSigTransaction again to network
txid = acl.send_transaction(lstx)
print("Transaction ID: " + txid)
