
from decimal import Decimal
import json
import os
import pytest
import sys
import threading
from time import sleep

import erc20token

# Ropsten configuration.
# the following address is set up in Ropsten and is pre-filled with ether and tokens.
ROPSTEN_ADDRESS = '0x4921a61F2733d9Cf265e13865820d7eb435DcBB2'
ROPSTEN_PRIVATE_KEY = 'dd5c6c0e12667d0563bc951e6eee5994cc786b6ce6a2192fd17b9d2bc810a25d'
ROPSTEN_CONTRACT = '0xEF2Fcc998847DB203DEa15fC49d0872C7614910C'
ROPSTEN_CONTRACT_ABI = json.loads('[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_newOwnerCandidate","type":"address"}],"name":"requestOwnershipTransfer","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"issueTokens","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"acceptOwnership","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"newOwnerCandidate","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"},{"indexed":true,"name":"spender","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_by","type":"address"},{"indexed":true,"name":"_to","type":"address"}],"name":"OwnershipRequested","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"}],"name":"OwnershipTransferred","type":"event"}]')  # noqa: E501
ROPSTEN_PROVIDER_ENDPOINT = 'http://159.89.240.246:8545'

# TestRpc configuration
# the following address is set up in TestRpc and is pre-filled with ether and tokens.
TESTRPC_ADDRESS = '0x8B455Ab06C6F7ffaD9fDbA11776E2115f1DE14BD'
TESTRPC_PRIVATE_KEY = '0x11c98b8fa69354b26b5db98148a5bc4ef2ebae8187f651b82409f6cefc9bb0b8'
TESTRPC_CONTRACT_FILE = './test/truffle_env/token_contract_address.txt'
TESTRPC_ABI_FILE = './test/truffle_env/build/contracts/TestToken.json'
TESTRPC_PROVIDER_ENDPOINT = 'http://localhost:8545'

TEST_KEYFILE = './test/test-keyfile.json'
TEST_PASSWORD = 'password'


@pytest.fixture(scope='session')
def testnet(ropsten):
    class Struct:
        """Handy variable holder"""
        def __init__(self, **entries): self.__dict__.update(entries)

    # if running on Ropsten, return predefined constants.
    if ropsten:
        return Struct(type='ropsten', address=ROPSTEN_ADDRESS, private_key=ROPSTEN_PRIVATE_KEY,
                      contract_address=ROPSTEN_CONTRACT, contract_abi=ROPSTEN_CONTRACT_ABI,
                      provider_endpoint_uri=ROPSTEN_PROVIDER_ENDPOINT)

    # using testrpc, needs truffle build environment.
    # testrpc contract address is set up during truffle deploy, and is passed in a file.
    contract_file = open(TESTRPC_CONTRACT_FILE)
    TESTRPC_CONTRACT = contract_file.read().strip()
    if not TESTRPC_CONTRACT:
        raise ValueError('contract address file {} is empty'.format(TESTRPC_CONTRACT_FILE))

    abi_file = open(TESTRPC_ABI_FILE).read()
    TESTRPC_CONTRACT_ABI = json.loads(abi_file)['abi']

    return Struct(type='testrpc', address=TESTRPC_ADDRESS, private_key=TESTRPC_PRIVATE_KEY,
                  contract_address=TESTRPC_CONTRACT, contract_abi=TESTRPC_CONTRACT_ABI,
                  provider_endpoint_uri=TESTRPC_PROVIDER_ENDPOINT)


def test_create_fail_empty_endpoint():
    with pytest.raises(erc20token.SdkConfigurationError,
                       match='either provider or provider endpoint must be provided'):
        erc20token.SDK()
    with pytest.raises(erc20token.SdkConfigurationError,
                       match='either provider or provider endpoint must be provided'):
        erc20token.SDK(provider_endpoint_uri='')


def test_create_fail_invalid_contract_address(testnet):
    with pytest.raises(erc20token.SdkConfigurationError,
                       match="invalid token contract address: '' is not an address"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri)
    with pytest.raises(erc20token.SdkConfigurationError,
                       match="invalid token contract address: '0xbad' is not an address"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address='0xbad')
    with pytest.raises(erc20token.SdkConfigurationError,
                       match="invalid token contract address: '0x4c6527c2BEB032D46cfe0648072cAb641cA0aA81' "
                             "has an invalid EIP55 checksum"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri,
                       contract_address='0x4c6527c2BEB032D46cfe0648072cAb641cA0aA81')


def test_create_fail_invalid_abi(testnet):
    with pytest.raises(erc20token.SdkConfigurationError, match="invalid token contract abi: 'abi' is not a list"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address)
    with pytest.raises(erc20token.SdkConfigurationError, match="invalid token contract abi: 'abi' is not a list"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi={})
    with pytest.raises(erc20token.SdkConfigurationError, match="invalid token contract abi: 'abi' is not a list"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi='bad')
    with pytest.raises(erc20token.SdkConfigurationError, match="invalid token contract abi: The elements of 'abi' "
                                                               "are not all dictionaries"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=['bad'])


def test_create_invalid_gas_params(testnet):
    with pytest.raises(erc20token.SdkConfigurationError, match='gas price must be either integer of float'):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=testnet.contract_abi, gas_price='bad')
    with pytest.raises(erc20token.SdkConfigurationError, match='gas price must be either integer of float'):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=testnet.contract_abi, gas_price='0x123')
    with pytest.raises(erc20token.SdkConfigurationError, match='gas limit must be integer'):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=testnet.contract_abi, gas_price=10, gas_limit='bad')


def test_create_fail_bad_endpoint(testnet):
    with pytest.raises(erc20token.SdkConfigurationError, match='cannot connect to provider endpoint'):
        erc20token.SDK(provider_endpoint_uri='bad', contract_address=testnet.address, contract_abi=testnet.contract_abi)


def test_create_fail_bad_private_key(testnet):
    with pytest.raises(erc20token.SdkConfigurationError, match='cannot load private key: Unexpected private key format.'
                                                               '  Must be length 32 byte string'):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=testnet.contract_abi, private_key='bad')


@pytest.mark.skipif(sys.version_info.major >= 3, reason="not yet supported in python 3")
def test_create_fail_keyfile(testnet):
    # file missing
    with pytest.raises(erc20token.SdkConfigurationError,
                       match="cannot load keyfile: \[Errno 2\] No such file or directory: 'missing.json'"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=testnet.contract_abi, keyfile='missing.json')

    # not json
    with open(TEST_KEYFILE, 'w+') as f:
        f.write('not json')
    with pytest.raises(erc20token.SdkConfigurationError, match="cannot load keyfile: No JSON object could be decoded"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=testnet.contract_abi, keyfile=TEST_KEYFILE)

    # json, but invalid format
    with open(TEST_KEYFILE, 'w+') as f:
        f.write('[]')
    with pytest.raises(erc20token.SdkConfigurationError, match="cannot load keyfile: invalid keyfile format"):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=testnet.contract_abi, keyfile=TEST_KEYFILE)

    # good keyfile, wrong password
    erc20token.create_keyfile(testnet.private_key, TEST_PASSWORD, TEST_KEYFILE)
    with pytest.raises(erc20token.SdkConfigurationError, match='cannot load keyfile: MAC mismatch. Password incorrect?'):
        erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                       contract_abi=testnet.contract_abi, keyfile=TEST_KEYFILE, password='wrong')
    os.remove(TEST_KEYFILE)


def test_sdk_not_configured(testnet):
    sdk = erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                         contract_abi=testnet.contract_abi)
    with pytest.raises(erc20token.SdkNotConfiguredError, match='private key not configured'):
        sdk.get_address()
    with pytest.raises(erc20token.SdkNotConfiguredError, match='private key not configured'):
        sdk.get_ether_balance()
    with pytest.raises(erc20token.SdkNotConfiguredError, match='private key not configured'):
        sdk.get_token_balance()
    with pytest.raises(erc20token.SdkNotConfiguredError, match='private key not configured'):
        sdk.send_ether('address', 100)
    with pytest.raises(erc20token.SdkNotConfiguredError, match='private key not configured'):
        sdk.send_tokens('address', 100)


def test_create_with_private_key(testnet):
    sdk = erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                         contract_abi=testnet.contract_abi, private_key=testnet.private_key)
    assert sdk
    assert sdk.web3
    assert sdk.token_contract
    assert sdk.private_key == testnet.private_key
    assert sdk.get_address() == testnet.address


@pytest.mark.skipif(sys.version_info.major >= 3, reason="not yet supported in python 3")
def test_create_with_keyfile(testnet):
    erc20token.create_keyfile(testnet.private_key, TEST_PASSWORD, TEST_KEYFILE)
    sdk = erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                         contract_abi=testnet.contract_abi, keyfile=TEST_KEYFILE, password=TEST_PASSWORD)
    assert sdk
    assert sdk.web3
    assert sdk.token_contract
    assert sdk.private_key == testnet.private_key
    assert sdk.get_address() == testnet.address
    os.remove(TEST_KEYFILE)


def test_create_with_gas_params(testnet):
    sdk = erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, contract_address=testnet.address,
                         contract_abi=testnet.contract_abi, private_key=testnet.private_key,
                         gas_price=10.1, gas_limit=10000)
    assert sdk
    assert sdk._tx_manager.gas_price == 10100000000
    assert sdk._tx_manager.gas_limit == 10000


@pytest.fixture(scope='session')
def test_sdk(testnet):
    sdk = erc20token.SDK(provider_endpoint_uri=testnet.provider_endpoint_uri, private_key=testnet.private_key,
                         contract_address=testnet.contract_address, contract_abi=testnet.contract_abi)
    assert sdk
    assert sdk.web3
    assert sdk.token_contract
    assert sdk.private_key == testnet.private_key
    assert sdk.get_address() == testnet.address
    assert sdk._tx_manager.gas_price == sdk.web3.eth.gasPrice
    return sdk


def test_get_address(test_sdk, testnet):
    assert test_sdk.get_address() == testnet.address


def test_get_ether_balance(test_sdk):
    balance = test_sdk.get_ether_balance()
    assert balance > 0


def test_get_address_ether_balance(test_sdk, testnet):
    with pytest.raises(ValueError, match="'0xBAD' is not an address"):
        test_sdk.get_address_ether_balance('0xBAD')
    balance = test_sdk.get_address_ether_balance(testnet.address)
    assert balance > 0


def test_get_token_balance(test_sdk):
    balance = test_sdk.get_token_balance()
    assert balance > 0


def test_get_address_token_balance(test_sdk, testnet):
    with pytest.raises(ValueError, match="'0xBAD' is not an address"):
        test_sdk.get_address_token_balance('0xBAD')
    balance = test_sdk.get_address_token_balance(testnet.address)
    assert balance > 0


def test_get_token_total_supply(test_sdk, testnet):
    total_supply = test_sdk.get_token_total_supply()
    if testnet.type == 'testrpc':
        assert total_supply == 1000
    else:
        assert total_supply > 1000000000


def test_send_ether_fail(test_sdk, testnet):
    with pytest.raises(ValueError, match='amount must be positive'):
        test_sdk.send_ether(testnet.address, 0)
    with pytest.raises(ValueError, match="'0xBAD' is not an address"):
        test_sdk.send_ether('0xBAD', 1)
    if testnet.type == 'ropsten':
        msg_match = 'Insufficient funds. The account you tried to send transaction from does not have enough funds'
    else:
        msg_match = "Error: sender doesn't have enough funds to send tx"
    with pytest.raises(ValueError, match=msg_match):
        test_sdk.send_ether(testnet.address, 100)


def test_send_tokens_fail(test_sdk, testnet):
    with pytest.raises(ValueError, match='amount must be positive'):
        test_sdk.send_tokens(testnet.address, 0)
    with pytest.raises(ValueError, match="'0xBAD' is not an address"):
        test_sdk.send_tokens('0xBAD', 1)

    # NOTE: sending more tokens than available will not cause immediate exception like with ether,
    # but will result in failed onchain transaction


def test_get_transaction_status(test_sdk, testnet):
    # unknown transaction
    tx_status = test_sdk.get_transaction_status('0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef')
    assert tx_status == erc20token.TransactionStatus.UNKNOWN

    # test with real transactions on Ropsten.
    # NOTE: depending on the Ropsten node configuration, these transactions can be already pruned.
    if testnet.type == 'ropsten':
        # successful ether transfer
        tx_status = test_sdk.get_transaction_status('0x86d51e5547b714232d39e86e86295c20e0241f38d9b828c080cc1ec561f34daf')
        assert tx_status == erc20token.TransactionStatus.SUCCESS
        # successful token transfer
        tx_status = test_sdk.get_transaction_status('0xb5101d58c1e51271837b5343e606b751512882e4f4b175b2f6dae68b7a42d4ab')
        assert tx_status == erc20token.TransactionStatus.SUCCESS
        # failed token transfer
        tx_status = test_sdk.get_transaction_status('0x7a3f2c843a04f6050258863dbea3fec3651b107baa5419e43adb6118478da36b')
        assert tx_status == erc20token.TransactionStatus.FAIL


def test_get_transaction_data(test_sdk, testnet):
    tx_data = test_sdk.get_transaction_data('0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef')
    assert tx_data.status == erc20token.TransactionStatus.UNKNOWN

    # some tests for Ropsten only
    if testnet.type == 'ropsten':
        # check ether transaction
        tx_id = '0x94d0ca03b3e5c132d3821c6fa416d74bab7e77969d5293a0df73ae7e15b46d7f'
        tx_data = test_sdk.get_transaction_data(tx_id)
        assert tx_data.status == erc20token.TransactionStatus.SUCCESS
        assert tx_data.to_address.lower() == testnet.address.lower()
        assert tx_data.to_address.lower() == testnet.address.lower()
        assert tx_data.ether_amount == Decimal('0.001')
        assert tx_data.token_amount == 0
        # check the number of confirmations
        tx = test_sdk.web3.eth.getTransaction(tx_id)
        assert tx and tx.get('blockNumber')
        tx_block_number = int(tx['blockNumber'])
        cur_block_number = int(test_sdk.web3.eth.blockNumber)
        calc_confirmations = cur_block_number - tx_block_number + 1
        tx_data = test_sdk.get_transaction_data(tx_id)
        assert tx_data.num_confirmations == calc_confirmations or tx_data.num_confirmations == calc_confirmations + 1


def monitor_ether_transactions(test_sdk, testnet):
    tx_statuses = {}

    def my_callback(tx_id, status, from_address, to_address, amount):
        if tx_id not in tx_statuses:  # not mine, skip it
            return
        assert from_address.lower() == testnet.address.lower()
        assert to_address.lower() == testnet.address.lower()
        assert amount == Decimal('0.001')
        tx_statuses[tx_id] = status

    with pytest.raises(ValueError, match='either from_address or to_address or both must be provided'):
        test_sdk.monitor_ether_transactions(my_callback)

    # start monitoring ether transactions
    test_sdk.monitor_ether_transactions(my_callback, from_address=testnet.address)

    # successful ether transfer
    tx_id = test_sdk.send_ether(testnet.address, Decimal('0.001'))
    tx_statuses[tx_id] = erc20token.TransactionStatus.UNKNOWN

    for wait in range(0, 30000):
        if tx_statuses[tx_id] > erc20token.TransactionStatus.UNKNOWN:
            break
        sleep(0.001)
    assert tx_statuses[tx_id] >= erc20token.TransactionStatus.PENDING
    tx_data = test_sdk.get_transaction_data(tx_id)
    assert tx_data.status >= erc20token.TransactionStatus.PENDING
    assert tx_data.from_address.lower() == testnet.address.lower()
    assert tx_data.to_address.lower() == testnet.address.lower()
    assert tx_data.ether_amount == Decimal('0.001')
    assert tx_data.token_amount == 0
    assert tx_data.num_confirmations >= 0

    for wait in range(0, 90):
        if tx_statuses[tx_id] > erc20token.TransactionStatus.PENDING:
            break
        sleep(1)
    assert tx_statuses[tx_id] == erc20token.TransactionStatus.SUCCESS
    tx_data = test_sdk.get_transaction_data(tx_id)
    assert tx_data.num_confirmations >= 1


def monitor_token_transactions(test_sdk, testnet):
    tx_statuses = {}

    def my_callback(tx_id, status, from_address, to_address, amount):
        if tx_id not in tx_statuses:  # not mine, skip it
            return
        assert from_address.lower() == testnet.address.lower()
        assert to_address.lower() == testnet.address.lower()
        tx_statuses[tx_id] = status

    with pytest.raises(ValueError, match='either from_address or to_address or both must be provided'):
        test_sdk.monitor_token_transactions(my_callback)

    # start monitoring token transactions from my address
    test_sdk.monitor_token_transactions(my_callback, to_address=testnet.address)

    # transfer more than available.
    # NOTE: with a standard ethereum node (geth, parity, etc), this will result in a failed onchain transaction.
    # With testrpc, this results in ValueError exception instead.
    if testnet.type == 'testrpc':
        with pytest.raises(ValueError, match='VM Exception while processing transaction: invalid opcode'):
            test_sdk.send_tokens(testnet.address, 10000000)
    else:
        tx_id = test_sdk.send_tokens(testnet.address, 10000000)
        tx_statuses[tx_id] = erc20token.TransactionStatus.UNKNOWN

        for wait in range(0, 30000):
            if tx_statuses[tx_id] > erc20token.TransactionStatus.UNKNOWN:
                break
            sleep(0.001)
        assert tx_statuses[tx_id] == erc20token.TransactionStatus.PENDING

        for wait in range(0, 90):
            if tx_statuses[tx_id] > erc20token.TransactionStatus.PENDING:
                break
            sleep(1)
        assert tx_statuses[tx_id] == erc20token.TransactionStatus.FAIL

    # successful token transfer
    tx_id = test_sdk.send_tokens(testnet.address, 10)
    tx_statuses[tx_id] = erc20token.TransactionStatus.UNKNOWN

    # wait for transaction status change
    for wait in range(0, 30000):
        if tx_statuses[tx_id] > erc20token.TransactionStatus.UNKNOWN:
            break
        sleep(0.001)
    assert tx_statuses[tx_id] >= erc20token.TransactionStatus.PENDING
    tx_data = test_sdk.get_transaction_data(tx_id)
    assert tx_data.status >= erc20token.TransactionStatus.PENDING
    assert tx_data.from_address.lower() == testnet.address.lower()
    assert tx_data.to_address.lower() == testnet.address.lower()
    assert tx_data.ether_amount == 0
    assert tx_data.token_amount == 10
    assert tx_data.num_confirmations >= 0

    # test transaction status
    tx_status = test_sdk.get_transaction_status(tx_id)
    assert tx_status >= erc20token.TransactionStatus.PENDING

    # wait for transaction status change
    for wait in range(0, 90):
        if tx_statuses[tx_id] > erc20token.TransactionStatus.PENDING:
            break
        sleep(1)
    assert tx_statuses[tx_id] == erc20token.TransactionStatus.SUCCESS
    tx_status = test_sdk.get_transaction_status(tx_id)
    assert tx_status == erc20token.TransactionStatus.SUCCESS
    tx_data = test_sdk.get_transaction_data(tx_id)
    assert tx_data.num_confirmations >= 1


def test_monitor_ether_transactions(test_sdk, testnet):
    if testnet.type == 'ropsten':
        pytest.skip("test is skipped in ropsten in favor of concurrent test")
    else:
        monitor_ether_transactions(test_sdk, testnet)


def test_monitor_token_transactions(test_sdk, testnet):
    if testnet.type == 'ropsten':
        pytest.skip("test is skipped in ropsten in favor of concurrent test")
    else:
        monitor_token_transactions(test_sdk, testnet)


def test_parallel_transactions(test_sdk, testnet):
    if testnet.type == 'testrpc':
        pytest.skip("concurrent test is skipped in testrpc")
        return
    t1 = threading.Thread(target=monitor_ether_transactions, args=(test_sdk, testnet))
    t2 = threading.Thread(target=monitor_token_transactions, args=(test_sdk, testnet))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()
    # below is a workaround for handling KeyboardInterrupt
    while True:
        t1.join(1)
        if not t1.isAlive():
            break
    while True:
        t2.join(1)
        if not t2.isAlive():
            break
