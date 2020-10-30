# stellar-cli - CLI tool for Stellar with support for custom tokens #

## Overview ##

This package provides a simple way to perform some basic operations on Stellar ledger. 
It fully supports **XLM and custom assets**.

The application can use a wallet defined in a local file as well as **Trezor**!


### Commands ###
This CLI client supports the following operations:
* **create_wallet** - create wallet and save keys (requires wallet_file / trezor)
* **show_wallet_address** - create wallet and save keys (requires wallet_file / trezor)
* **add_trust** - add trust for asset to wallet (requires wallet_file / trezor, asset code, asset issuer address)
* **list_balances** - display balances (requires wallet_file / trezor)
* **list_asset_balance** - display balances (requires wallet_file / trezor, asset code, asset issuer)
* **send_payment** - send payment (requires wallet_file / trezor, asset code, asset issuer address, payment amount, destination address)
* **list_transactions** - display transactions (requires wallet_file / trezor)

Assets can be specified as either -a ASSETCODE -i ISSUER_ADDRESS or -a ASSETCODE@domain.com (you don't need to specify the issuer address in this case)

Both test and production networks supported (see -t switch).

### Options ###
* **-t, --test** - test mode, uses testnet
* **-w, --wallet** - wallet file path
* **--trezor** - use attached Trezor
* **-a, --asset** - asset code (or ASSETCODE@domain.com format, eg. 'TCBT@thecryptobanker.com')
* **-i, --issuer** - issuer wallet address not needed if asset is specified as ASSETCODE@domain.com
* **-d, --destination** - wallet destination address
* **-p, --amount** - payment amount
* **--memo-id** - Stellar memo ID for payment TX
* **--memo-text** - Stellar memo Text for payment TX
* **--memo-hash** - Stellar memo Hash for payment TX
* **--qrlink** - generate an URL taking you to a QR code with the address of your wallet

## Examples ##

**Create wallet (and save it to file)**

`python stellar-cli.py -t create_wallet -w test_wallet_new.json`

**Show wallet address and QR Code URL**

`python stellar-cli.py show_wallet_address --trezor --qrlink`                                                                                                    

**Add trust for custom asset**

`python stellar-cli.py -t -w test_wallet.json add_trust -a TCBT -i GBQAHYCYVO62X33ILPC3ML35F5FWQAQ4IHYNCRDUIEKFOQKCXT7O6LCC`

**List balances**

`python stellar-cli.py -t -w test_wallet.json list_balances`

**List balance of a custom asset from Trezor**

`python stellar-cli.py list_asset_balance --trezor -a TCBT@thecryptobanker.com`

**List transactions**

`python stellar-cli.py -t -w test_wallet.json list_transactions`

**Send Payment - Custom Asset**

`python stellar-cli.py -t -w test_wallet.json send_payment -p 10 -d GCREGQJ46EELU5LAR2SSSR7CWIVJFB56YM73HXQUNR455KFPI6QAGSRY -a TCBT -i GBQAHYCYVO62X33ILPC3ML35F5FWQAQ4IHYNCRDUIEKFOQKCXT7O6LCC`

**Send Payment - Custom Asset with Memo**

`python stellar-cli.py send_payment --trezor -a TCBT@thecryptobanker.com -p 1 --memo-text tcbtpay123 -d GCT4F7MAJ5LB4VOGMEGACG2FKFWEEQ5RCPONB65HI7HK4V7IQD4YQ6ZK`

**Send Payment - Stellar Lumens (XLM)**

`python stellar-cli.py -t -w test_wallet.json send_payment -p 10 -d GATU7FV3IOUI4M6QWQXWSDUVTJJKD7ONJSBOJ4IJEETE5SPBW6JHAI22`

