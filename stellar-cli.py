import argparse
import sys
import stellarops.operations as operations

COMMAND_CREATE_WALLET = "create_wallet"
COMMAND_SHOW_WALLET_ADDRESS = "show_wallet_address"
COMMAND_ADD_TRUST = "add_trust"
COMMAND_LIST_BALANCES = "list_balances"
COMMAND_SEND_PAYMENT = "send_payment"
COMMAND_LIST_TRANSACTIONS = "list_transactions"
COMMAND_LIST_ASSET_BALANCE = "list_asset_balance"
COMMAND_SIGN_TX = "sign_tx"

SUPPORTED_COMMANDS = {
    COMMAND_CREATE_WALLET: "",
    COMMAND_SHOW_WALLET_ADDRESS: "",
    COMMAND_ADD_TRUST: "",
    COMMAND_LIST_BALANCES: "",
    COMMAND_LIST_ASSET_BALANCE: "",
    COMMAND_SEND_PAYMENT: "",
    COMMAND_LIST_TRANSACTIONS: "",
    COMMAND_SIGN_TX: ""

}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, choices=SUPPORTED_COMMANDS.keys(),
                        help="command for the client. supported options are: {}".format(', '.join(SUPPORTED_COMMANDS.keys())))
    parser.add_argument("-t", "--test", help="use test network", action="store_true")
    parser.add_argument("-a", "--asset", type=str, help="asset code")
    parser.add_argument("-i", "--issuer", type=str, help="issuer wallet address")
    parser.add_argument("-p", "--amount", type=float, help="payment amount")
    parser.add_argument("-d", "--destination", type=str, help="destination wallet address")
    parser.add_argument("-s", "--source", type=str,
                        help="source wallet address (if signing with your wallet for this source account)")
    parser.add_argument("--qrlink", action="store_true", help="generate qr code link")
    parser.add_argument("--justsign", action="store_true", help="just sign the transaction, don't submit it")
    parser.add_argument("--mnemonic", action="store_true", help="generate address from mnemonic")
    parser.add_argument("--vzero", action="store_true", help="use version zero of stellar TX")
    parser.add_argument("--timeout", type=int, help="Transaction validity in seconds")
    group_wallet = parser.add_mutually_exclusive_group(required=True)
    group_wallet.add_argument("-w", "--wallet", type=str, help="path to wallet file")
    group_wallet.add_argument("--trezor", action="store_true", help="use an attached Trezor")
    group_memo = parser.add_mutually_exclusive_group(required=False)
    group_memo.add_argument("--memo-id", type=int, help="ID memo for Stellar transaction")
    group_memo.add_argument("--memo-text", type=str, help="Text memo for Stellar transaction")
    group_memo.add_argument("--memo-hash", type=str, help="Hash memo for Stellar transaction")
    args = parser.parse_args()
    test_mode = args.test
    command = args.command
    wallet_file = args.wallet
    trezor_mode = args.trezor
    vzero = args.vzero
    timeout = args.timeout
    generate_qr_code_link = args.qrlink
    use_mnemonic = args.mnemonic
    if command == COMMAND_CREATE_WALLET:
        if not trezor_mode:
            operations.create_stellar_wallet(wallet_file=wallet_file, generate_qr_code_link=generate_qr_code_link,
                                             use_mnemonic=use_mnemonic)
        else:
            print("Trezor wallet must be already initialized. Will retrieve public key wallet now")
            operations.retrieve_trezor_public_key(generate_qr_code_link=generate_qr_code_link)
    elif command == COMMAND_SHOW_WALLET_ADDRESS:
        if not trezor_mode:
            operations.retrieve_stellar_wallet_public_key(wallet_file=wallet_file,
                                                          generate_qr_code_link=generate_qr_code_link)
        else:
            operations.retrieve_trezor_public_key(generate_qr_code_link=generate_qr_code_link)
    elif command == COMMAND_ADD_TRUST:
        asset = args.asset
        issuer = args.issuer
        if asset is None:
            print("Missing asset code.")
            sys.exit(1)
        if issuer is None:
            if '@' in asset:
                asset, issuer, domain = operations.get_asset_from_domain(asset)
            else:
                print("Missing issuer address.")
                sys.exit(1)
        operations.add_trust(wallet_file=wallet_file, asset=asset, issuer=issuer, test_mode=test_mode,
                             trezor_mode=trezor_mode, vzero=vzero, timeout=timeout)
    elif command == COMMAND_LIST_BALANCES:
        operations.list_balances(wallet_file=wallet_file, test_mode=test_mode, trezor_mode=trezor_mode)
    elif command == COMMAND_LIST_ASSET_BALANCE:
        asset = args.asset
        issuer = args.issuer
        domain = None
        if asset is not None and issuer is None and '@' in asset:
            asset, issuer, domain = operations.get_asset_from_domain(asset_with_domain=asset)
            if asset is None:
                print("Could not identify asset. Please provide issuer or use -a ASSET_CODE@domain.com format")
                sys.exit(1)
        if asset is not None and issuer is None:
            print("Could not identify asset. Please provide issuer or use -a ASSET_CODE@domain.com format")
            sys.exit(1)
        operations.list_asset_balance(wallet_file=wallet_file, asset=asset, issuer=issuer, domain=domain,
                                      test_mode=test_mode, trezor_mode=trezor_mode)
    elif command == COMMAND_SEND_PAYMENT:
        asset = args.asset
        issuer = args.issuer
        destination = args.destination
        amount = args.amount
        memo_text = args.memo_text
        memo_id = args.memo_id
        memo_hash = args.memo_hash
        source = args.source
        just_sign = args.justsign
        if asset is not None and issuer is None and '@' in asset:
            asset, issuer, domain = operations.get_asset_from_domain(asset_with_domain=asset)
            if asset is None:
                sys.exit(1)
        if asset is not None and issuer is None:
            print("Could not identify asset. Please provide issuer or use -a ASSET_CODE@domain.com format")
            sys.exit(1)
        if destination is None:
            print("Missing destination address.")
            sys.exit(1)
        if amount is None:
            print("Missing amount.")
            sys.exit(1)
        operations.send_payment(wallet_file=wallet_file, asset=asset, issuer=issuer, amount=amount,
                                destination=destination, source=source,
                                memo_text=memo_text, memo_id=memo_id, memo_hash=memo_hash,
                                test_mode=test_mode,
                                trezor_mode=trezor_mode,
                                just_sign=just_sign, vzero=vzero, timeout=timeout)
    elif command == COMMAND_SIGN_TX:
        transaction_xdr = input("Paste your TX XDR DATA:").strip()
        just_sign = args.justsign
        if transaction_xdr is None or len(transaction_xdr) == 0:
            "Missing TX XDR data."
        operations.sign_transaction_from_xdr(wallet_file=wallet_file, transaction_xdr=transaction_xdr,
                                             test_mode=test_mode, trezor_mode=trezor_mode, just_sign=just_sign,
                                             vzero=vzero)
    elif command == COMMAND_LIST_TRANSACTIONS:
        operations.list_transactions(wallet_file=wallet_file, test_mode=test_mode, trezor_mode=trezor_mode)

