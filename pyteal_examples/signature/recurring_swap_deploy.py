#!/usr/bin/env python3

import base64
from nacl import encoding, hash
import params
import re
import time
import uuid

from algosdk import algod
from algosdk.future import transaction

from pyteal import *

from recurring_swap import recurring_swap


# ------- generate provider's account -----------------------------------------------
key_fn = str(uuid.uuid4()) + ".key"
execute(["algokey", "generate", "-f", key_fn])
stdout, stderr = execute(["algokey", "export", "-f", key_fn])
print("generated key file {}".format(key_fn))

if stderr != "":
    print(stderr)
    raise

result = re.search(r"key: \w+", stdout)
provider_addr = result.group(0)[5:]
print("provider addr: {}".format(provider_addr))

# ------- instantiate template, compile teal source, get escrow address -------------

program = recurring_swap(tmpl_provider=Addr(provider_addr))
teal_source = compileTeal(program, mode=Mode.Signature, version=2)
# print(teal_source)

# compile teal
teal_base = str(uuid.uuid4())
teal_file = teal_base + ".teal"
with open(teal_file, "w+") as f:
    f.write(teal_source)
lsig_fname = teal_base + ".tealc"

stdout, stderr = execute(["goal", "clerk", "compile", "-o", lsig_fname, teal_file])

if stderr != "":
    print(stderr)
    raise
elif len(stdout) < 59:
    print("error in compile teal")
    raise

result = re.search(r": \w+", stdout)
escrow_addr = result.group(0)[2:]
print("Dispense at least 202000 microAlgo to {}".format(escrow_addr))
input("Make sure you did that. Press Enter to continue...")

# now, as a provider, you can withdraw Algo from the escrow if you sign the first valid
acl = algod.AlgodClient(params.algod_token, params.algod_address)

sp = acl.suggested_params_as_object()
first_valid = sp.first
data = first_valid.to_bytes(8, byteorder="big")
lease = hash.sha256(data)
lease_bytes = encoding.HexEncoder.decode(lease)
print("first valid: {}".format(first_valid))

txn = transaction.PaymentTxn(escrow_addr, sp, provider_addr, 100000, lease=lease_bytes)

with open(lsig_fname, "rb") as f:
    teal_bytes = f.read()
lsig = transaction.LogicSig(teal_bytes)
lstx = transaction.LogicSigTransaction(txn, lsig)

assert lstx.verify()

# send LogicSigTransaction to network
transaction.write_to_file([lstx], "r_s_1.txn")

stdout, stderr = execute(
    [
        "goal",
        "clerk",
        "tealsign",
        "--data-b64",
        base64.b64encode(data),
        "--lsig-txn",
        "r_s_1.txn",
        "--keyfile",
        key_fn,
        "--set-lsig-arg-idx",
        "0",
    ]
)
if stderr != "":
    print(stderr)
    raise

print(stdout)

lstx = transaction.retrieve_from_file("r_s_1.txn")
txid = acl.send_transactions(lstx)

print("1st withraw Succesfull! txid:{}".format(txid))

# at least sleep to the next round
time.sleep(6)

sp = acl.suggested_params_as_object()
first_valid = sp.first
data = first_valid.to_bytes(8, byteorder="big")
lease = hash.sha256(data)
lease_bytes = encoding.HexEncoder.decode(lease)

print("first valid: {}".format(first_valid))

txn = transaction.PaymentTxn(escrow_addr, sp, provider_addr, 100000, lease=lease_bytes)

with open(lsig_fname, "rb") as f:
    teal_bytes = f.read()
lsig = transaction.LogicSig(teal_bytes)
lstx = transaction.LogicSigTransaction(txn, lsig)

assert lstx.verify()

# send LogicSigTransaction to network
transaction.write_to_file([lstx], "r_s_2.txn")

stdout, stderr = execute(
    [
        "goal",
        "clerk",
        "tealsign",
        "--data-b64",
        base64.b64encode(data),
        "--lsig-txn",
        "r_s_2.txn",
        "--keyfile",
        key_fn,
        "--set-lsig-arg-idx",
        "0",
    ]
)
if stderr != "":
    print(stderr)
    raise

print(stdout)

lstx = transaction.retrieve_from_file("r_s_2.txn")
txid = acl.send_transactions(lstx)
print("2nd withraw Succesfull! txid:{}".format(txid))
