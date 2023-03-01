import base64
import os
import uuid

from algosdk import account, algod, mnemonic, transaction
from pyteal import compileTeal, Mode, periodic_payment

# Update to your node and algod credentials
algod_address = os.environ['ALGOD_ADDRESS']
algod_token = os.environ['ALGOD_TOKEN']

# Recover the account that is wanting to delegate signature
mnemonic_secret = "patrol crawl rule faculty enemy sick reveal embody trumpet win shy zero ill draw swim excuse tongue under exact baby moral kite spring absent double"
sk = mnemonic.to_private_key(mnemonic_secret)
addr = account.address_from_private_key(sk)

print(f"Dispense at least 201000 microAlgo to {addr}")
input("Make sure you did that. Press Enter to continue...")

# compile and get TEAL code as bytes
teal_source = periodic_payment()
compiled = compileTeal(teal_source, mode=Mode.Signature, version=2)
teal_bytes = compiled.encode()

# write TEAL to file
teal_file = f"{uuid.uuid4()}.teal"
with open(teal_file, "wb") as f:
    f.write(teal_bytes)

# compile TEAL
result = transaction.compile(teal_file)

# get suggested parameters
params = algod.AlgodClient(algod_token, algod_address).suggested_params()

# create the logic signature transaction
txn = transaction.LogicSigTransaction(
    sender=addr,
    sp=params,
    program=result["result"],
)

# sign the transaction with the secret key
txn.sign(sk)

# write the transaction to file
txns = [txn]
transaction.write_to_file(txns, "p_pay.stxn")

# send the transaction
tx_id = algod.AlgodClient(algod_token, algod_address).send_transactions(txns)
print(f"Transaction ID: {tx_id}")
