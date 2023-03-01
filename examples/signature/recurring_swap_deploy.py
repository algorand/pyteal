#!/usr/bin/env python3

import base64
import uuid

from algosdk import account, algod, encoding, mnemonic, transaction
from pyteal import *

from recurring_swap import recurring_swap

# compile teal
teal_source = compileTeal(recurring_swap(), mode=Mode.Signature, version=2)
teal_bytes = base64.b64decode(teal_source)

# create algod clients
algod_client = algod.AlgodClient("<algod-token>", "<algod-address>")

# Recover the account that is wanting to delegate signature
passphrase = "your-account-passphrase-here"
sk = mnemonic.to_private_key(passphrase)
sender = account.address_from_private_key(sk)

# get suggested parameters
params = algod_client.suggested_params()
params.fee = 1000

# create the transaction
txn = transaction.PaymentTxn(
    sender=sender,
    fee=params.fee,
    first=params.first,
    last=params.last,
    gh=params.genesis_hash,
    receiver=sender,
    amount=0,
    close_remainder_to=sender,
    lease=base64.b64decode("oR/ACMN6EDwCwstJcrNQrgI6T3F6NQPDnmYVcLrz1v4="),
)

# create the logic signature
lsig = transaction.LogicSig(teal_bytes)

# sign the logic signature with an account sk
lsig.sign(sk)

# create the logic signature transaction
lstx = transaction.LogicSigTransaction(txn, lsig)

# write the transaction to file
transaction.write_to_file([lstx], "<filename>.stxn")

# send the transaction
txid = algod_client.send_transaction(lstx)
print("Transaction ID: " + txid)
