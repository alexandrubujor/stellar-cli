from stellar_sdk.asset import Asset
from stellar_sdk.keypair import Keypair
from stellar_sdk.network import Network
from stellar_sdk.server import Server
from stellar_sdk.transaction_builder import TransactionBuilder
from stellar_sdk.exceptions import BaseHorizonError
from .fileops import load_wallet, write_wallet
import os
import json


def get_network_settings(test_mode):
    if test_mode:
        return {
            "network_passphrase": Network.TESTNET_NETWORK_PASSPHRASE,
            "horizon_url": "https://horizon-testnet.stellar.org"
        }
    else:
        return {
            "network_passphrase": Network.PUBLIC_NETWORK_PASSPHRASE,
            "horizon_url": "https://horizon.stellar.org"
        }


def create_stellar_wallet(wallet_file):
    if os.path.exists(wallet_file):
        print("Error: Wallet file already exists! Will not overwrite it for security reasons.")
        return
    else:
        keypair = Keypair.random()
        public_key = keypair.public_key
        private_key = keypair.secret
        write_wallet(wallet_file=wallet_file, private_key=private_key, public_key=public_key)
        response = {
            "public_key": public_key,
            "message": "A new keypair was generated for you and saved in {}. Initialize it by sending at least 1 XLM to {}".format(wallet_file, public_key)
        }
        print(json.dumps(response, indent=4))


def add_trust(wallet_file, asset, issuer, test_mode=True):
    (private_key, public_key) = load_wallet(wallet_file=wallet_file)
    network_settings = get_network_settings(test_mode=test_mode)
    stellar_asset = Asset(asset, issuer)
    k = Keypair.from_secret(secret=private_key)
    server = Server(network_settings.get("horizon_url"))
    account = server.load_account(account_id=k.public_key)
    transaction = (
        TransactionBuilder(
            source_account=account,
            network_passphrase=network_settings.get("network_passphrase"),
            base_fee=100,
        )
            .append_change_trust_op(
            asset_code=stellar_asset.code, asset_issuer=stellar_asset.issuer,
        )
        .set_timeout(100)
        .build()
    )
    transaction.sign(k)
    try:
        transaction_resp = server.submit_transaction(transaction)
        print("{}".format(json.dumps(transaction_resp, indent=4)))
    except BaseHorizonError as e:
        print(f"Error: {e}")


def list_balances(wallet_file, test_mode=True):
    (private_key, public_key) = load_wallet(wallet_file=wallet_file)
    network_settings = get_network_settings(test_mode=test_mode)
    k = Keypair.from_secret(secret=private_key)
    server = Server(network_settings.get("horizon_url"))
    response = server.accounts().account_id(account_id=k.public_key).call()
    balances = response.get("balances")
    print(json.dumps(balances, indent=4))


def list_transactions(wallet_file, test_mode=True):
    (private_key, public_key) = load_wallet(wallet_file=wallet_file)
    network_settings = get_network_settings(test_mode=test_mode)
    k = Keypair.from_secret(secret=private_key)
    server = Server(network_settings.get("horizon_url"))
    response = server.transactions().for_account(account_id=k.public_key).call()
    print(json.dumps(response, indent=4))


def send_payment(wallet_file, asset, issuer, amount, destination, test_mode=True):
    (private_key, public_key) = load_wallet(wallet_file=wallet_file)
    network_settings = get_network_settings(test_mode=test_mode)
    k = Keypair.from_secret(secret=private_key)
    server = Server(network_settings.get("horizon_url"))
    account = server.load_account(account_id=k.public_key)
    if asset is None or issuer is None:
        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=network_settings.get("network_passphrase"),
                base_fee=100,
            )
            .append_payment_op(
                destination=destination,
                amount=str(amount),
            )
            .set_timeout(100)
            .build()
        )
    else:
        stellar_asset = Asset(asset, issuer)
        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=network_settings.get("network_passphrase"),
                base_fee=100,
            )
            .append_payment_op(
                destination=destination,
                amount=str(amount),
                asset_code=stellar_asset.code,
                asset_issuer=stellar_asset.issuer,
            )
            .set_timeout(100)
            .build()
        )
    transaction.sign(k)
    try:
        transaction_resp = server.submit_transaction(transaction)
        print("{}".format(json.dumps(transaction_resp, indent=4)))
    except BaseHorizonError as e:
        print(f"Error: {e}")