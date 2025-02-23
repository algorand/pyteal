import base64
from typing import Tuple
from algosdk import mnemonic, transaction, account
from algosdk.v2client import algod
from pyteal import *

# example: LSIG_SIMPLE_ESCROW
def donation_escrow(benefactor):
    Fee = Int(1000)

    # Only the benefactor account can withdraw from this escrow
    program = And(
        Txn.type_enum() == TxnType.Payment,
        Txn.fee() <= Fee,
        Txn.receiver() == Addr(benefactor),
        Global.group_size() == Int(1),
        Txn.rekey_to() == Global.zero_address(),
    )

    # Mode.Signature specifies that this is a smart signature
    return compileTeal(program, Mode.Signature, version=5)


# example: LSIG_SIMPLE_ESCROW

# example: LSIG_SIMPLE_ESCROW_INIT
rando_addr, _ = account.generate_account()
teal_program = donation_escrow(rando_addr)
# example: LSIG_SIMPLE_ESCROW_INIT


# example: LSIG_SIMPLE_SETUP
# user declared account mnemonics
benefactor_mnemonic = "REPLACE WITH YOUR OWN MNEMONIC"
sender_mnemonic = "REPLACE WITH YOUR OWN MNEMONIC"


# user declared algod connection parameters. Node must have EnableDeveloperAPI set to true in its config
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
# example: LSIG_SIMPLE_SETUP

# example: LSIG_SIMPLE_HELPERS
# helper function to compile program source
def compile_smart_signature(
    client: algod.AlgodClient, source_code: str
) -> Tuple[str, str]:
    compile_response = client.compile(source_code)
    return compile_response["result"], compile_response["hash"]


# example: LSIG_SIMPLE_HELPERS


# example: LSIG_SIMPLE_SEED_PAYMENT
def payment_transaction(
    creator_mnemonic: str, amt: int, rcv: str, algod_client: algod.AlgodClient
) -> dict:
    creator_pk = mnemonic.to_private_key(creator_mnemonic)
    creator_address = account.address_from_private_key(creator_pk)

    params = algod_client.suggested_params()
    unsigned_txn = transaction.PaymentTxn(creator_address, params, rcv, amt)
    signed = unsigned_txn.sign(creator_pk)

    txid = algod_client.send_transaction(signed)
    pmtx = transaction.wait_for_confirmation(algod_client, txid, 5)
    return pmtx


# example: LSIG_SIMPLE_SEED_PAYMENT


# example: LSIG_SIMPLE_WITHDRAW
def lsig_payment_txn(
    encoded_program: str, amt: int, rcv: str, algod_client: algod.AlgodClient
):
    # Create an lsig object using the compiled, b64 encoded program
    program = base64.b64decode(encoded_program)
    lsig = transaction.LogicSigAccount(program)

    # Create transaction with the lsig address as the sender
    params = algod_client.suggested_params()
    unsigned_txn = transaction.PaymentTxn(lsig.address(), params, rcv, amt)

    # sign the transaction using the logic
    stxn = transaction.LogicSigTransaction(unsigned_txn, lsig)
    tx_id = algod_client.send_transaction(stxn)
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 10)
    return pmtx


# example: LSIG_SIMPLE_WITHDRAW


# example: LSIG_SIMPLE_USAGE
def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # define private keys
    private_key = mnemonic.to_private_key(benefactor_mnemonic)
    receiver_public_key = account.address_from_private_key(private_key)

    print("Compiling Donation Smart Signature......")

    stateless_program_teal = donation_escrow(receiver_public_key)
    escrow_result, escrow_address = compile_smart_signature(
        algod_client, stateless_program_teal
    )

    print("Program:", escrow_result)
    print("LSig Address: ", escrow_address)

    print("Activating Donation Smart Signature......")

    # Activate escrow contract by sending 2 algo and 1000 microalgo for transaction fee from creator
    amt = 2001000
    payment_transaction(sender_mnemonic, amt, escrow_address, algod_client)

    print("Withdraw from Donation Smart Signature......")

    # Withdraws 1 ALGO from smart signature using logic signature.
    withdrawal_amt = 1000000
    lsig_payment_txn(escrow_result, withdrawal_amt, receiver_public_key, algod_client)


# example: LSIG_SIMPLE_USAGE


if __name__ == "__main__":
    main()
