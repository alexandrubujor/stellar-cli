from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder, Transaction, TransactionEnvelope
from stellar_sdk.exceptions import BaseHorizonError
from stellar_sdk.xdr.decorated_signature import DecoratedSignature
from stellar_sdk.xdr.signature_hint import SignatureHint
from stellar_sdk.xdr.signature import Signature
from trezorlib import stellar as trezor_stellar
from trezorlib import tools as trezor_tools
from trezorlib import messages
from trezorlib import client
from .fileops import load_wallet, write_wallet
import os
import base64
import json
import toml
import requests


BASE_FEE = 5000


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


def create_stellar_wallet(wallet_file, use_mnemonic=False, generate_qr_code_link=False):
    if os.path.exists(wallet_file):
        print("Error: Wallet file already exists! Will not overwrite it for security reasons.")
        return
    else:
        if use_mnemonic:
            mnemonic = Keypair.generate_mnemonic_phrase(strength=256)
            keypair = Keypair.from_mnemonic_phrase(mnemonic)
        else:
            keypair = Keypair.random()
            mnemonic = "NOT_USED"
        public_key = keypair.public_key
        private_key = keypair.secret
        write_wallet(wallet_file=wallet_file, private_key=private_key, public_key=public_key)
        response = {
            "public_key": public_key,
            "mnemonic": mnemonic,
            "message": "A new keypair was generated for you and saved in {}. Initialize it by sending at least 1 XLM to {}".format(wallet_file, public_key)
        }
        print(json.dumps(response, indent=4))
        if generate_qr_code_link:
            print(generate_qr_code_url(public_key))


def retrieve_stellar_wallet_public_key(wallet_file, generate_qr_code_link=False):
    (private_key, public_key) = load_wallet(wallet_file=wallet_file)
    print(public_key)
    if generate_qr_code_link:
        print(generate_qr_code_url(public_key))


def add_trust(wallet_file, asset, issuer, test_mode=True, trezor_mode=False, vzero=False, timeout=3600):
    network_settings = get_network_settings(test_mode=test_mode)
    if timeout is None:
        timeout = 3600
    v1_mode = not vzero
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
            base_fee=BASE_FEE,
            v1=v1_mode
        )
        .append_change_trust_op(
            asset=Asset(code=stellar_asset.code, issuer=stellar_asset.issuer),
        )
        .set_timeout(timeout)
        .build()
    )
    if not trezor_mode:
        transaction.sign(k)
    else:
        transaction = sign_trezor_transaction(transaction, k,
                                              network_passphrase=network_settings.get("network_passphrase"))
    try:
        transaction_resp = server.submit_transaction(transaction)
        print("{}".format(json.dumps(transaction_resp, indent=4)))
    except BaseHorizonError as e:
        print("Error: {}".format(str(e)))


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


def list_asset_balance(wallet_file, asset, issuer, domain=None, test_mode=False, trezor_mode=False):
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
    for b in balances:
        balance = b.get("balance")
        asset_code = b.get("asset_code")
        asset_issuer = b.get("asset_issuer")
        if asset_code == asset and asset_issuer == issuer:
            if asset_code is None and asset_issuer is None:
                print("{} XLM".format(balance))
            else:
                if domain is None:
                    print("{} {} issued by {}".format(balance, asset_code, asset_issuer))
                else:
                    print("{} {}@{} issued by {}".format(balance, asset_code, domain, asset_issuer))


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


def send_payment(wallet_file, asset, issuer, amount, destination,
                 source=None,
                 memo_text=None, memo_id=None, memo_hash=None,
                 test_mode=True, trezor_mode=False, just_sign=False, vzero=False, timeout=3600):
    network_settings = get_network_settings(test_mode=test_mode)
    if timeout is None:
        timeout = 3600
    v1_mode = not vzero
    if not trezor_mode:
        (private_key, public_key) = load_wallet(wallet_file=wallet_file)
        k = Keypair.from_secret(secret=private_key)
    else:
        public_key = get_trezor_public_key()
        k = Keypair.from_public_key(public_key=public_key)
        v1_mode = False
    server = Server(network_settings.get("horizon_url"))
    if source is None:
        account = server.load_account(account_id=k.public_key)
    else:
        account = server.load_account(account_id=source)
    if asset is None or issuer is None:
        tb = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=network_settings.get("network_passphrase"),
                base_fee=BASE_FEE,
                v1=v1_mode
            )
            .append_payment_op(
                asset=Asset.native(),
                destination=destination,
                amount=str(amount),
            )
            .set_timeout(timeout)
        )
    else:
        stellar_asset = Asset(asset, issuer)
        tb = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=network_settings.get("network_passphrase"),
                base_fee=BASE_FEE,
                v1=v1_mode
            )
            .append_payment_op(
                destination=destination,
                amount=str(amount),
                asset=Asset(code=stellar_asset.code, issuer=stellar_asset.issuer)
            )
            .set_timeout(timeout)
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
    if just_sign:
        print("TX SIGNED DATA:\n{}".format(transaction.to_xdr()))
    else:
        broadcast_tx(transaction=transaction, test_mode=test_mode)


def get_asset_data_from_domain(asset_code, asset_domain):
    toml_file = "https://{}/.well-known/stellar.toml".format(asset_domain)
    print("Loading TOML content from: {}\n".format(toml_file))
    toml_string = requests.get(url=toml_file).text
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


def generate_qr_code_url(public_key):
    url = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={}".format(public_key)
    return url


def retrieve_trezor_public_key(generate_qr_code_link=False):
    public_key = get_trezor_public_key()
    print(get_trezor_public_key())
    if generate_qr_code_link:
        print(generate_qr_code_url(public_key))


def sign_trezor_transaction(transaction, public_key, network_passphrase):
    xdr_data = transaction.to_xdr()
    address_n = trezor_tools.parse_path(trezor_stellar.DEFAULT_BIP32_PATH)
    tx, operations = trezor_stellar.parse_transaction_bytes(base64.b64decode(xdr_data))
    resp = trezor_stellar.sign_tx(client.get_default_client(), tx, operations, address_n, network_passphrase)
    signature = resp.signature
    s_element = DecoratedSignature(SignatureHint(public_key.signature_hint()), Signature(signature))
    transaction.signatures.append(s_element)
    return transaction


def show_transaction_data(transaction):
    print("\nYou are about to sign a new transaction with the following details:\n\n{}\n".format(str(transaction.transaction)))
    print("The following operations are included in this transaction:\n")
    for o in transaction.transaction.operations:
        print("{}\n".format(str(o)))
    confirmation = input("Would you like to sign this? (Enter SIGN to sign or anything else to cancel):")
    if confirmation.strip() == "SIGN":
        print("Signing\n")
        return True
    else:
        print("Signing cancelled\n")
        return False


def show_transaction_data_before_submit(transaction):
    print("\nYou are about to submit a new transaction with the following details:\n\n{}\n".format(str(transaction.transaction)))
    print("The following operations are included in this transaction:\n")
    for o in transaction.transaction.operations:
        print("{}\n".format(str(o)))
    confirmation = input("Would you like to submit this? (Enter SUBMIT to submit or anything else to cancel):")
    if confirmation.strip() == "SUBMIT":
        print("Broadcasting\n")
        return True
    else:
        print("Broadcasting cancelled\n")
        return False


def sign_transaction_from_xdr(wallet_file, transaction_xdr, test_mode=True, trezor_mode=False, just_sign=False,
                              vzero=False):
    network_settings = get_network_settings(test_mode=test_mode)
    if not trezor_mode:
        transaction = TransactionEnvelope.from_xdr(transaction_xdr,
                                                   network_passphrase=network_settings.get("network_passphrase"))
        confirmation = show_transaction_data(transaction)
        if not confirmation:
            return
        (private_key, public_key) = load_wallet(wallet_file=wallet_file)
        k = Keypair.from_secret(secret=private_key)
        transaction.sign(k)
    else:
        transaction = TransactionEnvelope.from_xdr(transaction_xdr,
                                                   network_passphrase=network_settings.get("network_passphrase"))
        confirmation = show_transaction_data(transaction)
        if not confirmation:
            return
        public_key = get_trezor_public_key()
        k = Keypair.from_public_key(public_key=public_key)
        transaction = sign_trezor_transaction(transaction=transaction, public_key=k,
                                              network_passphrase=network_settings.get("network_passphrase"))
    if just_sign:
        print("TX SIGNED DATA:\n{}".format(transaction.to_xdr()))
    else:
        broadcast_tx(transaction=transaction, test_mode=test_mode)


def submit_transaction(transaction_xdr, test_mode=True, vzero=False):
    network_settings = get_network_settings(test_mode=test_mode)
    transaction = TransactionEnvelope.from_xdr(transaction_xdr,
                                               network_passphrase=network_settings.get("network_passphrase"))
    confirmation = show_transaction_data_before_submit(transaction)
    if not confirmation:
        return
    else:
        broadcast_tx(transaction=transaction, test_mode=test_mode)


def broadcast_tx(transaction, test_mode=True):
    network_settings = get_network_settings(test_mode=test_mode)
    server = Server(network_settings.get("horizon_url"))
    try:
        transaction_resp = server.submit_transaction(transaction)
        print("{}".format(json.dumps(transaction_resp, indent=4)))
    except BaseHorizonError as e:
        print("Error: {}".format(str(e)))


def get_asset_from_domain(asset_with_domain):
    if asset_with_domain is not None and '@' in asset_with_domain:
        asset_code, asset_domain = asset_with_domain.split('@')
        asset_code, asset_issuer, asset_domain = get_asset_data_from_domain(asset_code=asset_code,
                                                                            asset_domain=asset_domain)
        if asset_code is None:
            print("Could not identify token on this domain.")
            return None, None, None
        else:
            print("We discovered the following token: {} @ {} issued by {}".format(asset_code,
                                                                                   asset_domain,
                                                                                   asset_issuer))
            asset = asset_code
            issuer = asset_issuer
            return asset, issuer, asset_domain


def translate_address(account_name, account_domain):
    toml_file = "https://{}/.well-known/stellar.toml".format(account_domain)
    print("Loading TOML content from: {}\n".format(toml_file))
    toml_string = requests.get(url=toml_file).text
    toml_data = toml.loads(toml_string)
    federation_server_url = toml_data.get("FEDERATION_SERVER")
    print("Using FEDERATION Server: {}\n".format(federation_server_url))
    query_url = "{}?q={}*{}&type=name".format(federation_server_url, account_name, account_domain)
    r = requests.get(url=query_url)
    r.raise_for_status()
    response_json = json.loads(r.text)
    address = response_json.get("account_id")
    return address


def process_destination_address(address):
    if address is None:
        print("Missing address.\n")
        return None
    full_address = address.strip()
    if '*' in address:
        account_name, account_domain = full_address.split('*', 1)
        try:
            translated_address = translate_address(account_name=account_name, account_domain=account_domain)
            print("{} --- translated to ---> {}\n".format(full_address, translated_address))
            return translated_address
        except Exception as e:
            print("Could not identify address using Federation server. Error: {}\n".format(str(e)))
            return None
    else:
        return full_address
