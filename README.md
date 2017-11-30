
# ERC20 Token Python SDK 
[![Build Status](https://travis-ci.com/kinfoundation/erc20token-sdk-python.svg?token=f7PF9BYUzqkMQU5JpUvN)](https://travis-ci.com/kinfoundation/erc20token-sdk-python)

## Disclaimer

The SDK is still in beta. No warranties are given. Use on your own discretion.

## Requirements.

Make sure you have Python 2 >=2.7.9.

## Installation 

```sh
pip install git+https://github.com/kinfoundation/erc20token-sdk-python.git
```

### Installation in Google App Engine Python Standard Environment
[GAE Python Standard environment](https://cloud.google.com/appengine/docs/standard/) executes Python 
application code using a pre-loaded Python interpreter in a safe sandboxed environment. The interpreter cannot 
load Python services with C code; it is a "pure" Python environment. However, the required
[web3 package](https://pypi.python.org/pypi/web3/) requires other packages that are natively implemented, namely
[pysha3](https://pypi.python.org/pypi/pysha3) and [cytoolz](https://pypi.python.org/pypi/cytoolz).
In order to overcome this limitation, do the following:
1. Replace the `sha3.py` installed by pysha3 with the [attached sha3.py](sha3.py.alt).
2. Replace the installed `cytoolz` package with the `toolz` package.

You will still not be able to use the functions `monitor_ether_transactions` and `monitor_token_transactions`
because they launch a thread, and GAE Standard applications cannot spawn threads.


## Usage

### Initialization

```python
import erc20token

# Init SDK with default parameters
# default parameters:
#   `provider` is `web3.providers.HTTPProvider`
#   `provider_endpoint_uri` is `http://159.89.240.147:8545`
#   `contract_address` is KIN production contract `0x818fc6c2ec5986bc6e2cbf00939d90556ab12ce5`
#   `contract_abi` is KIN production contract ABI
# Note: this is useful for anonymous blockchain access, when your private key is not needed.
token_sdk = erc20token.SDK()

# Init SDK with my private key and default parameters
token_sdk = erc20token.SDK(private_key='a60baaa34ed125af0570a3df7d4cd3e80dd5dc5070680573f8de0ecfc1957575')

# Init SDK with my keyfile and default parameters
# First, create a keyfile from my private key
erc20token.create_keyfile('a60baaa34ed125af0570a3df7d4cd3e80dd5dc5070680573f8de0ecfc1957575', 'my password', 'keyfile.json')
# Init SDK with this keyfile
token_sdk = erc20token.SDK(keyfile='keyfile.json', password='my password')

# Init SDK with custom parameters
token_sdk = erc20token.SDK(provider_endpoint_uri='JSON-RPC endpoint URI', private_key='my private key',
                       contract_address='my contract address', contract_abi='abi of my contract as json')
````
For more examples, see the [SDK test file](test/test_sdk.py). The file also contains pre-defined values for testing
with testrpc and Ropsten.


### Get Wallet Details
```python
# Get my public address. The address is derived from the private key the SDK was inited with.
address = token_sdk.get_address()
```

### Getting Account Balance
```python
# Get Ether balance of my account
eth_balance = token_sdk.get_ether_balance()

# Get token balance of my account
token_balance = token_sdk.get_token_balance()

# Get Ether balance of some address
eth_balance = token_sdk.get_address_ether_balance('address')

# Get token balance of some address
token_balance = token_sdk.get_address_token_balance('address')
```

### Sending Coin
```python
# Send Ether from my account to some address. The amount is in Ether.
tx_id = token_sdk.send_ether('address', 10)

# Send tokens from my account to some address. The amount is in tokens.
tx_id = token_sdk.send_tokens('address', 10)
```

### Transaction Monitoring
```python
# Get transaction status
tx_status = token_sdk.get_transaction_status(tx_id)
# Returns one of:
#   erc20token.TransactionStatus.UNKNOWN
#   erc20token.TransactionStatus.PENDING
#   erc20token.TransactionStatus.SUCCESS
#   erc20token.TransactionStatus.FAIL

# Get transaction details
tx_data = token_sdk.get_transaction_data(tx_id)
# Returns an erc20token.TransactionData object containing the following fields:
# from_address - the address this transaction was sent from
# to_address   - the address this transaction was sent to. For token transactions, this is the decoded recipient address.
# ether_amount - the amount of transferred Ether. 0 for token transactions.
# token_amount - the amount of transferred tokens. 0 for Ether transactions.
# status       - the transaction status, see above.
# num_confirmations - the number of confirmations for this transaction:
#   -1 if transaction is not found
#    0 if transaction is pending
#   >0 if transaction is confirmed

# Setup monitoring callback
tx_statuses = {}
def mycallback(tx_id, status, from_address, to_address, amount):
    tx_statuses[tx_id] = status
  
# Monitor token transactions from me 
token_sdk.monitor_token_transactions(mycallback, from_address=token_sdk.get_address())

# Send tokens
tx_id = token_sdk.send_tokens('to address', 10)

# In a second or two, the transaction enters the pending queue
for wait in range(0, 5000):
    if tx_statuses[tx_id] > erc20token.TransactionStatus.UNKNOWN:
        break
    sleep(0.001)
assert tx_statuses[tx_id] >= erc20token.TransactionStatus.PENDING

# Wait until transaction is confirmed 
for wait in range(0, 90):
    if tx_statuses[tx_id] > erc20token.TransactionStatus.PENDING:
        break
    sleep(1)
assert tx_statuses[tx_id] == erc20token.TransactionStatus.SUCCESS
```

## Support & Discussion

## License
Code released under [GPLv2 license](LICENSE)

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for SDK contributing guidelines. 

