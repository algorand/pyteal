import base64
from nacl import encoding, hash
import params

import time


from algosdk import algod, account, encoding as algosdk_encoding, transaction
from pyteal import *

from recurring_swap import recurring_swap

# ------- generate provider's account -----------------------------------------------
private_key, provider_addr = account.generate_account()
print("provider addr: {}".format(provider_addr))

# ------- instantiate template, compile teal source, get escrow address -------------

program = recurring_swap(tmpl_provider=Addr(provider_addr))
teal_source = compileTeal(program, mode=Mode.Signature, version=2)
# print(teal_source)

# compile teal
teal_bytes = teal_source.encode()
escrow_lsig = transaction.LogicSig(account.logic_sign(teal_bytes))

escrow_addr = algosdk_encoding.encode_address(escrow_lsig.address())
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

lstx = transaction.LogicSigTransaction(txn, escrow_lsig)

assert lstx.verify()

txid = acl.send_transaction(lstx)
print("1st withdraw Succesfull! txid:{}".format(txid))

# at least sleep to the next round
time.sleep(6)

sp = acl.suggested_params_as_object()
first_valid = sp.first
data = first_valid.to_bytes(8, byteorder="big")
lease = hash.sha256(data)
lease_bytes = encoding.HexEncoder.decode(lease)

print("first valid: {}".format(first_valid))

txn = transaction.PaymentTxn(escrow_addr, sp, provider_addr, 100000, lease=lease_bytes)

lstx = transaction.LogicSigTransaction(txn, escrow_lsig)

assert lstx.verify()

txid = acl.send_transaction(lstx)
print("2nd withdraw Succesfull! txid:{}".format(txid))
