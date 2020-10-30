from stellar_sdk.asset import Asset
from stellar_sdk.keypair import Keypair
from stellar_sdk.network import Network
from stellar_sdk.server import Server
from stellar_sdk.transaction_builder import TransactionBuilder
from stellar_sdk.exceptions import BaseHorizonError
from stellar_sdk.xdr import Xdr
from trezorlib import stellar as trezor_stellar
from trezorlib import tools as trezor_tools
from trezorlib import messages
from trezorlib import client
from .fileops import load_wallet, write_wallet
import os
import base64
import json
import toml
import urllib.request


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


def retrieve_stellar_wallet_public_key(wallet_file):
    (private_key, public_key) = load_wallet(wallet_file=wallet_file)
    print(public_key)


def add_trust(wallet_file, asset, issuer, test_mode=True, trezor_mode=False):
    network_settings = get_network_settings(test_mode=test_mode)
    v1_mode = True
    if not trezor_mode:
        (private_key, public_key) = load_wallet(wallet_file=wallet_file)
        k = Keypair.from_secret(secret=private_key)
    else:
        public_key = get_trezor_public_key()
        k = Keypair.from_public_key(public_key=public_key)
        v1_mode = False
    server = Server(network_settings.get("horizon_url"))
    stellar_asset = Asset(asset, issuer)
    account = server.load_account(account_id=k.public_key)
    transaction = (
        TransactionBuilder(
            source_account=account,
            network_passphrase=network_settings.get("network_passphrase"),
            base_fee=100,
            v1=v1_mode
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


def list_balances(wallet_file, test_mode=True, trezor_mode=False):
    network_settings = get_network_settings(test_mode=test_mode)
    if not trezor_mode:
        (private_key, public_key) = load_wallet(wallet_file=wallet_file)
        k = Keypair.from_secret(secret=private_key)
    else:
        public_key = get_trezor_public_key()
        k = Keypair.from_public_key(public_key=public_key)
    server = Server(network_settings.get("horizon_url"))
    response = server.accounts().account_id(account_id=k.public_key).call()
    balances = response.get("balances")
    print(json.dumps(balances, indent=4))


def list_transactions(wallet_file, test_mode=True, trezor_mode=False):
    network_settings = get_network_settings(test_mode=test_mode)
    if not trezor_mode:
        (private_key, public_key) = load_wallet(wallet_file=wallet_file)
        k = Keypair.from_secret(secret=private_key)
    else:
        public_key = get_trezor_public_key()
        k = Keypair.from_public_key(public_key=public_key)
    server = Server(network_settings.get("horizon_url"))
    response = server.transactions().for_account(account_id=k.public_key).call()
    print(json.dumps(response, indent=4))


def send_payment(wallet_file, asset, issuer, amount, destination, memo_text=None, memo_id=None, memo_hash=None,
                 test_mode=True, trezor_mode=False):
    network_settings = get_network_settings(test_mode=test_mode)
    v1_mode = True
    if not trezor_mode:
        (private_key, public_key) = load_wallet(wallet_file=wallet_file)
        k = Keypair.from_secret(secret=private_key)
    else:
        public_key = get_trezor_public_key()
        k = Keypair.from_public_key(public_key=public_key)
        v1_mode = False
    server = Server(network_settings.get("horizon_url"))
    account = server.load_account(account_id=k.public_key)
    if asset is None or issuer is None:
        tb = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=network_settings.get("network_passphrase"),
                base_fee=100,
                v1=v1_mode
            )
            .append_payment_op(
                destination=destination,
                amount=str(amount),
            )
            .set_timeout(100)
        )
    else:
        stellar_asset = Asset(asset, issuer)
        tb = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=network_settings.get("network_passphrase"),
                base_fee=100,
                v1=v1_mode
            )
            .append_payment_op(
                destination=destination,
                amount=str(amount),
                asset_code=stellar_asset.code,
                asset_issuer=stellar_asset.issuer,
            )
            .set_timeout(100)
        )
    if memo_text is not None:
        tb.add_text_memo(memo_text=memo_text)
    elif memo_id is not None:
        tb.add_id_memo(memo_id=memo_id)
    elif memo_hash is not None:
        tb.add_hash_memo(memo_hash=memo_hash)
    transaction = tb.build()
    if not trezor_mode:
        transaction.sign(k)
    else:
        transaction = sign_trezor_transaction(transaction, k,
                                              network_passphrase=network_settings.get("network_passphrase"))
    try:
        transaction_resp = server.submit_transaction(transaction)
        print("{}".format(json.dumps(transaction_resp, indent=4)))
    except BaseHorizonError as e:
        print(f"Error: {e}")


def get_asset_data_from_domain(asset_code, asset_domain):
    toml_file = "https://{}/.well-known/stellar.toml".format(asset_domain)
    toml_string = urllib.request.urlopen(toml_file).read().decode()
    toml_data = toml.loads(toml_string)
    currencies = toml_data.get("CURRENCIES")
    for c in currencies:
        if c.get("code") == asset_code:
            asset_issuer = c.get("issuer")
            return asset_code, asset_issuer, asset_domain
    return None, None, None


def get_trezor_public_key():
    address = trezor_stellar.DEFAULT_BIP32_PATH
    address_n = trezor_tools.parse_path(address)
    m = messages.StellarGetAddress(address_n=address_n)
    c = client.get_default_client()
    r = c.call(m)
    return r.address


def retrieve_trezor_public_key():
    print(get_trezor_public_key())


def sign_trezor_transaction(transaction, public_key, network_passphrase):
    xdr_data = transaction.to_xdr()
    address_n = trezor_tools.parse_path(trezor_stellar.DEFAULT_BIP32_PATH)
    tx, operations = trezor_stellar.parse_transaction_bytes(base64.b64decode(xdr_data))
    resp = trezor_stellar.sign_tx(client.get_default_client(), tx, operations, address_n, network_passphrase)
    signature = resp.signature
    s_element = Xdr.types.DecoratedSignature(public_key.signature_hint(), signature)
    transaction.signatures.append(s_element)
    return transaction
