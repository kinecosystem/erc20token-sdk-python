
# ERC20 Token Python SDK 
[![Build Status](https://travis-ci.org/kinfoundation/erc20token-sdk-python.svg)](https://travis-ci.org/kinfoundation/erc20token-sdk-python) [![Coverage Status](https://codecov.io/gh/kinfoundation/erc20token-sdk-python/branch/master/graph/badge.svg?token=dOvV9K8oFe)](https://codecov.io/gh/kinfoundation/erc20token-sdk-python)

## Disclaimer

The SDK is still in beta. No warranties are given, use on your own discretion.

## Requirements.

Make sure you have Python 2 >=2.7.9.

## Installation 

```sh
pip install erc20token
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

To initialize the SDK, you need to provide the following parameters:
- [JSON-RPC API](https://github.com/ethereum/wiki/wiki/JSON-RPC)  endpoint URI of your Ethereum node 
(for example, http://mainnet.infura.io)
- The address of your token contract
- The ABI of your token contract as json
- (optionally) either your private key, or a keyfile+password 

If you do not provide a public key or a keyfile, you will NOT be able to use the following functions:
`get_address`, `get_ether_balance`, `get_token_balance`, `send_ether`, `send_tokens`.


```python
import erc20token
import json

# Init SDK without a private key (for generic blockchain queries)
token_sdk = erc20token.SDK(provider_endpoint_uri='http://localhost:8545', 
                       contract_address='0x04f72aa40046c5fb3b143aaba3ab64d1a82410a7', 
                       contract_abi=json.loads(contract_abi))
                       
# Init SDK with a private key
token_sdk = erc20token.SDK(provider_endpoint_uri='http://localhost:8545', 
                       private_key='a60baaa34ed125af0570a3df7d4cd3e80dd5dc5070680573f8de0ecfc1957575',
                       contract_address='0x04f72aa40046c5fb3b143aaba3ab64d1a82410a7', 
                       contract_abi=json.loads(contract_abi))
                       
# Init SDK with a keyfile
# First, create a keyfile from my private key
erc20token.create_keyfile('a60baaa34ed125af0570a3df7d4cd3e80dd5dc5070680573f8de0ecfc1957575', 
                          'my password', 'keyfile.json')
# Then, init SDK with the keyfile
token_sdk = erc20token.SDK(provider_endpoint_uri='http://localhost:8545', 
                       keyfile='keyfile.json', password='my password',
                       contract_address='0x04f72aa40046c5fb3b143aaba3ab64d1a82410a7', 
                       contract_abi=json.loads(contract_abi))
````
For more examples, see the [SDK test file](test/test_sdk.py). The file also contains pre-defined values for testing
with testrpc and Ropsten.


### Get Wallet Details
```python
# Get my public address. The address is derived from the private key the SDK was inited with.
address = token_sdk.get_address()
```

### Get the Number of Issued Tokens
```python
# Get total supply of tokens
total_supply = token_sdk.get_token_total_supply()
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
You can send Ether or tokens:
```python
# Send Ether from my account to some address. The amount is in Ether.
tx_id = token_sdk.send_ether('address', 10)

# Send tokens from my account to some address. The amount is in tokens.
tx_id = token_sdk.send_tokens('address', 10)
```
If you do not have enough Ether, `send_ether` will raise an exception.
However, if you do not have enough tokens, `send_tokens` will finish successfully. The transaction will end up as 
FAILED on the blockchain, consuming all your gas.

### Getting Transaction Data
```python
# Get transaction status
tx_status = token_sdk.get_transaction_status(tx_id)
# Returns one of:
#   erc20token.TransactionStatus.UNKNOWN = 0
#   erc20token.TransactionStatus.PENDING = 1
#   erc20token.TransactionStatus.SUCCESS = 2
#   erc20token.TransactionStatus.FAIL    = 3

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
```

### Transaction Monitoring

You can monitor Ether and token transactions, either from some address or to some address, or both. Provide a 
callback to the monitoring function, to be called when the transaction status changes.
NOTE: PENDING status can be received several times, it means the transaction changes blocks.

```python
# Setup monitoring callback
tx_statuses = {}
def mycallback(tx_id, status, from_address, to_address, amount):
    tx_statuses[tx_id] = status
  
# Monitor token transactions from me 
token_sdk.monitor_token_transactions(mycallback, from_address=token_sdk.get_address())

# Send tokens
tx_id = token_sdk.send_tokens('to address', 10)

# In a short while, the transaction enters the pending queue
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

## Limitations

### Ethereum Node

The SDK requires that some of the features in [JSON-RPC API](https://github.com/ethereum/wiki/wiki/JSON-RPC) 
implementation of Ethereum node work correctly: specifically handling filters and pending transactions. Due to a very 
dynamic state of development of Ethereum nodes, the support for these features is not yet solid and varies from 
vendor to vendor and from version to version. After some experimentation, we settled on the
[Parity Ethereum Node](https://www.parity.io/), version **v1.8.3-beta**.

If you are running several Ethereum nodes behind a load balancer, you should enable 
[connection stickiness](https://stackoverflow.com/questions/10494431/sticky-and-non-sticky-sessions) on the 
load balancer: The SDK keeps a state (running filters) on the node it is using and stickiness ensures that requests 
will reach the same node. In addition, sending a transaction to one node will not make it immediately visible on 
another node, so stickiness ensures consistent transaction-state when polling on nodes.

### GAE Standard

As was mentioned earlier, you will not be able to use the functions `monitor_ether_transactions` and 
`monitor_token_transactions`, because they launch a thread, and GAE Standard applications cannot spawn threads.

### SDK Limitations

1. The SDK only support tokens with 18 decimals, which is the most common number of decimal places. When using tokens
with a different number of decimals, you will need to make your own conversions.
2. The SDK supports only a limited subset of [ERC20 Token Standard](https://theethereum.wiki/w/index.php/ERC20_Token_Standard),
namely `totalSupply`, `transfer` and `balanceOf` functions. Additional functionality will be added as needed. 
Your PRs are welcome!
3. The SDK initialization with keyfile and password is currently supported only in Python 2.7.

## License
The code is currently released under [GPLv2 license](LICENSE) due to some GPL-licensed packages it uses. In the 
future, we will make an effort to use a less restrictive license.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for SDK contributing guidelines. 

