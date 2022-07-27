import base64
import os

from examples.application.abi.algobank import (
    approval_program,
    clear_state_program,
    contract,
)

from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
    AccountTransactionSigner,
)
from algosdk.logic import get_application_address
from algosdk import account, mnemonic

algod_token = os.environ["ALGOD_TOKEN"]
algod_address = os.environ["ALGOD_ADDRESS"]

creator_mnemonic = os.environ["ACCOUNT_1"]
user_mnemonic = os.environ["ACCOUNT_2"]


def compile_program(client: algod.AlgodClient, teal_source: str) -> bytes:
    response = client.compile(teal_source)
    return base64.b64decode(response["result"])


def create_app(
    client: algod.AlgodClient, creator_addr: str, creator_private_key: str
) -> int:
    compiled_approval_program = compile_program(client, approval_program)
    compiled_clear_state_program = compile_program(client, clear_state_program)

    # get node suggested parameters
    params = client.suggested_params()

    # declare application state storage (immutable)
    # 1 global int, the "lost" amount
    global_schema = transaction.StateSchema(num_uints=1, num_byte_slices=0)
    # 1 local int, the "balance" amount
    local_schema = transaction.StateSchema(num_uints=1, num_byte_slices=0)

    # create unsigned transaction
    create_txn = transaction.ApplicationCreateTxn(
        sender=creator_addr,
        on_complete=transaction.OnComplete.NoOpOC,
        global_schema=global_schema,
        local_schema=local_schema,
        approval_program=compiled_approval_program,
        clear_program=compiled_clear_state_program,
        note=b"Hello Proof of State stream!",
        sp=params,
    )

    # sign create transaction
    signed_create_txn = create_txn.sign(creator_private_key)
    create_txid = signed_create_txn.transaction.get_txid()

    # send create transaction
    client.send_transaction(signed_create_txn)

    create_tx_info = transaction.wait_for_confirmation(
        client, create_txid, wait_rounds=10
    )
    app_id = create_tx_info["application-index"]

    app_addr = get_application_address(app_id)

    funding_txn = transaction.PaymentTxn(
        sender=creator_addr,
        receiver=app_addr,
        amt=100_000,  # account minimum balance
        sp=params,
    )

    # sign funding transaction
    signed_funding_txn = funding_txn.sign(creator_private_key)
    funding_txid = signed_funding_txn.get_txid()

    # send funding transaction
    client.send_transaction(signed_funding_txn)

    transaction.wait_for_confirmation(client, funding_txid, wait_rounds=10)

    return app_id


def deposit(
    client: algod.AlgodClient,
    app_id: int,
    sender_addr: str,
    sender_private_key: str,
    amount: int,
    opt_in: bool = False,
) -> None:
    # get node suggested parameters
    params = client.suggested_params()

    composer = AtomicTransactionComposer()

    payment = TransactionWithSigner(
        txn=transaction.PaymentTxn(
            sender=sender_addr,
            receiver=get_application_address(app_id),
            amt=amount,
            sp=params,
        ),
        signer=AccountTransactionSigner(sender_private_key),
    )

    composer.add_method_call(
        app_id=app_id,
        sender=sender_addr,
        signer=AccountTransactionSigner(sender_private_key),
        method=contract.get_method_by_name("deposit"),
        method_args=[payment, sender_addr],
        on_complete=transaction.OnComplete.OptInOC
        if opt_in
        else transaction.OnComplete.NoOpOC,
        sp=params,
    )

    composer.execute(client, wait_rounds=10)


def getBalance(
    client: algod.AlgodClient,
    app_id: int,
    sender_addr: str,
    sender_private_key: str,
    user_addr: str,
) -> int:
    # get node suggested parameters
    params = client.suggested_params()

    composer = AtomicTransactionComposer()

    composer.add_method_call(
        app_id=app_id,
        sender=sender_addr,
        signer=AccountTransactionSigner(sender_private_key),
        method=contract.get_method_by_name("getBalance"),
        method_args=[user_addr],
        sp=params,
    )

    result = composer.execute(client, wait_rounds=10)

    assert len(result.abi_results) == 1

    method_result = result.abi_results[0]

    assert method_result.decode_error is None
    assert type(method_result.return_value) is int

    return method_result.return_value


def withdraw(
    client: algod.AlgodClient,
    app_id: int,
    sender_addr: str,
    sender_private_key: str,
    receiver: str,
    amount: int,
) -> None:
    # get node suggested parameters
    params = client.suggested_params()

    params.flat_fee = True
    params.fee = 2 * params.min_fee

    composer = AtomicTransactionComposer()

    composer.add_method_call(
        app_id=app_id,
        sender=sender_addr,
        signer=AccountTransactionSigner(sender_private_key),
        method=contract.get_method_by_name("withdraw"),
        method_args=[amount, receiver],
        sp=params,
    )

    composer.execute(client, wait_rounds=10)


def main() -> None:
    # initialize an algod client
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # get private keys
    creator_private_key = mnemonic.to_private_key(creator_mnemonic)
    creator_addr = account.address_from_private_key(creator_private_key)
    user_private_key = mnemonic.to_private_key(user_mnemonic)
    user_addr = account.address_from_private_key(user_private_key)

    # create a new AlgoBank application
    app_id = create_app(algod_client, creator_addr, creator_private_key)

    # deposit 1 Algo (1,000,000 microAlgos)
    deposit(algod_client, app_id, user_addr, user_private_key, 1_000_000, opt_in=True)

    balance_after_deposit = getBalance(
        algod_client, app_id, creator_addr, creator_private_key, user_addr
    )
    # balance should be 1 Algo
    assert balance_after_deposit == 1_000_000

    # withdraw 0.25 Algos
    withdraw(algod_client, app_id, user_addr, user_private_key, user_addr, 250_000)

    balance_after_withdrawal = getBalance(
        algod_client, app_id, creator_addr, creator_private_key, user_addr
    )
    # balance should be 0.75 Algos
    assert balance_after_withdrawal == 750_000


if __name__ == "__main__":
    main()
