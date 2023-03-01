import base64
import uuid

from algosdk import account, algod, mnemonic, transaction
from algosdk.future import transaction as future
from pyteal import *

# set account information and get algod client
algod_token = "your_algod_token"
algod_address = "http://localhost:4001"
acl = algod.AlgodClient(algod_token, algod_address)

# Recover the account that is wanting to delegate signature
passphrase = "patrol crawl rule faculty enemy sick reveal embody trumpet win shy zero ill draw swim excuse tongue under exact baby moral kite spring absent double"
sk = mnemonic.to_private_key(passphrase)
addr = account.address_from_private_key(sk)
print(f"Dispense at least 201000 microAlgo to {addr}")
input("Make sure you did that. Press Enter to continue...")

# compile the Teal program
teal_source = compileTeal(periodic_payment(), mode=Mode.Signature, version=2)
response = acl.compile(teal_source.encode("utf-8"))
program = response["result"]

# create the logic signature
lsig = transaction.LogicSig(program)

# sign the logic signature with an account sk
lsig.sign(sk)

# get suggested parameters
params = acl.suggested_params()
gen = params["genesis_id"]
gh = params["genesis_hash"]
start_round = params["last_round"] - (params["last_round"] % 1000)
end_round = start_round + 1000
fee = 1000
amount = 200000
receiver = "ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM"
lease = base64.b64decode("y9OJ5MRLCHQj8GqbikAUKMBI7hom+SOj8dlopNdNHXI=")

# create the transaction
txn = future.PaymentTxn(addr, fee, start_round, end_round, gh, receiver, amount, flat_fee=True, lease=lease)

# create the logic signature transaction
lstx = future.LogicSigTransaction(txn, lsig)

# write to file
txns = [lstx]
transaction.write_to_file(txns, "p_pay.stxn")

# send the transaction to the network
txid = acl.send_transaction(lstx)
print(f"Transaction ID: {txid}")
