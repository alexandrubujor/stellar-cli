# stellar-cli - CLI tool for stellar ledger #

## Overview ##

This package provides a simple way to perform some basic operations on Stellar ledger. 
It supports XLM and custom defined assets.


### Commands ###
This CLI client supports the following operations:
* **create_wallet** - create wallet and save keys (requires wallet_file)
* **add_trust** - add trust for asset to wallet (requires wallet_file, asset code, asset issuer address)
* **list_balances** - display balances (requires wallet_file)
* **send_payment** - send payment (requires wallet_file, asset code, asset issuer address, payment amount, destination address)
* **list_transactions** - display transactions (requires wallet_file)

It supports both test and production networks (see -t switch)

### Options ###
* **-t, --test** - test mode, uses testnet
* **-w, --wallet** - wallet file path
* **-a, --asset** - asset code
* **-i, --issuer** - issuer wallet address
* **-d, --destination** - wallet destination address
* **-p, --amount** - payment amount

## Examples ##

**Create wallet (and save it to file)**

`python stellar-cli.py -t create_wallet -w test_wallet_new.json`

**Add trust for custom asset**

`python stellar-cli.py -t -w test_wallet.json add_trust -a TCBT -i GBQAHYCYVO62X33ILPC3ML35F5FWQAQ4IHYNCRDUIEKFOQKCXT7O6LCC`

**List balances**

`python stellar-cli.py -t -w test_wallet.json list_balances`

**List transactions**

`python stellar-cli.py -t -w test_wallet.json list_transactions`

**Send Payment - Custom Asset**

`python stellar-cli.py -t -w test_wallet.json send_payment -p 10 -d GCREGQJ46EELU5LAR2SSSR7CWIVJFB56YM73HXQUNR455KFPI6QAGSRY -a TCBT -i GBQAHYCYVO62X33ILPC3ML35F5FWQAQ4IHYNCRDUIEKFOQKCXT7O6LCC`

**Send Payment - Stellar Lumens (XLM)**

`python stellar-cli.py -t -w test_wallet.json send_payment -p 10 -d GATU7FV3IOUI4M6QWQXWSDUVTJJKD7ONJSBOJ4IJEETE5SPBW6JHAI22`