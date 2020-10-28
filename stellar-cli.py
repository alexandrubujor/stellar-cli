import argparse
import sys
import stellarops.operations as operations

COMMAND_CREATE_WALLET = "create_wallet"
COMMAND_ADD_TRUST = "add_trust"
COMMAND_LIST_BALANCES = "list_balances"
COMMAND_SEND_PAYMENT = "send_payment"
COMMAND_LIST_TRANSACTIONS = "list_transactions"

SUPPORTED_COMMANDS = {
    COMMAND_CREATE_WALLET: "",
    COMMAND_ADD_TRUST: "",
    COMMAND_LIST_BALANCES: "",
    COMMAND_SEND_PAYMENT: "",
    COMMAND_LIST_TRANSACTIONS: ""
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, choices=SUPPORTED_COMMANDS.keys(),
                        help="command for the client. cupported options are: {}".format(', '.join(SUPPORTED_COMMANDS.keys())))
    parser.add_argument("-t", "--test", help="use test network", action="store_true")
    parser.add_argument("-w", "--wallet", type=str, required=True, help="path to wallet file")
    parser.add_argument("-a", "--asset", type=str, help="asset code")
    parser.add_argument("-i", "--issuer", type=str, help="issuer wallet address")
    parser.add_argument("-p", "--amount", type=float, help="payment amount")
    parser.add_argument("-d", "--destination", type=str, help="destination wallet address")
    args = parser.parse_args()
    test_mode = args.test
    command = args.command
    wallet_file = args.wallet
    if command == COMMAND_CREATE_WALLET:
        operations.create_stellar_wallet(wallet_file=wallet_file)
    elif command == COMMAND_ADD_TRUST:
        asset = args.asset
        issuer = args.issuer
        if asset is None:
            print("Missing asset code.")
            sys.exit(1)
        if issuer is None:
            if '@' in asset:
                asset_code, asset_domain = asset.split('@')
                asset_code, asset_issuer, asset_domain = operations.get_asset_data_from_domain(asset_code=asset_code,
                                                                                               asset_domain=asset_domain)
                if asset_code is None:
                    print("Could not identify token on this domain.")
                    sys.exit(1)
                else:
                    print("We discovered the following token: {} @ {} issued by {}".format(asset_code,
                                                                                           asset_domain,
                                                                                           asset_issuer))
                    asset = asset_code
                    issuer = asset_issuer
            else:
                print("Missing issuer address.")
                sys.exit(1)
        operations.add_trust(wallet_file=wallet_file, asset=asset, issuer=issuer, test_mode=test_mode)
    elif command == COMMAND_LIST_BALANCES:
        operations.list_balances(wallet_file=wallet_file, test_mode=test_mode)
    elif command == COMMAND_SEND_PAYMENT:
        asset = args.asset
        issuer = args.issuer
        destination = args.destination
        amount = args.amount
        if asset is not None and '@' in asset:
            asset_code, asset_domain = asset.split('@')
            asset_code, asset_issuer, asset_domain = operations.get_asset_data_from_domain(asset_code=asset_code,
                                                                                           asset_domain=asset_domain)
            if asset_code is None:
                print("Could not identify token on this domain.")
                sys.exit(1)
            else:
                print("We discovered the following token: {} @ {} issued by {}".format(asset_code,
                                                                                       asset_domain,
                                                                                       asset_issuer))
                asset = asset_code
                issuer = asset_issuer
        if destination is None:
            print("Missing destination address.")
            sys.exit(1)
        if amount is None:
            print("Missing amount.")
            sys.exit(1)
        operations.send_payment(wallet_file=wallet_file, asset=asset, issuer=issuer, amount=amount,
                                destination=destination,
                                test_mode=test_mode)
    elif command == COMMAND_LIST_TRANSACTIONS:
        operations.list_transactions(wallet_file=wallet_file, test_mode=test_mode)

