


from algosdk import algod, account, mnemonic, transaction
from algosdk.future import template
from pyteal import *

# Compile and sign the smart contract
teal_source = compileTeal(periodic_payment(), mode=Mode.Signature, version=2)
compiled = compileProgram(teal_source)

# Create an Algod client
acl = algod.AlgodClient(
    algod_token="YOUR_ALGOD_TOKEN", algod_address="YOUR_ALGOD_ADDRESS"
)

# Recover the account that is wanting to delegate signature
passphrase = "patrol crawl rule faculty enemy sick reveal embody trumpet win shy zero ill draw swim excuse tongue under exact baby moral kite spring absent double"
sk = mnemonic.to_private_key(passphrase)
addr = account.address_from_private_key(sk)

# Get suggested parameters for the transaction
params = acl.suggested_params()
params.flat_fee = True
params.fee = 1000

# Create the contract account
contract = template.LogicSig(compiled)

# Create a payment transaction
receiver = "ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM"
amount = 200000
lease = base64.b64decode("y9OJ5MRLCHQj8GqbikAUKMBI7hom+SOj8dlopNdNHXI=")
txn = transaction.PaymentTxn(addr, params, receiver, amount, lease)

# Sign the transaction with the contract account
stxn = txn.sign(contract)

# Send the transaction to the network
txid = acl.send_transaction(stxn)
print("Transaction ID:", txid)
