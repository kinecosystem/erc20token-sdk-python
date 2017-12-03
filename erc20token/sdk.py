# -*- coding: utf-8 -*

# Copyright (C) 2017 Kin Foundation


import threading
from time import sleep

from eth_abi import decode_abi
from eth_keys import keys
from eth_keys.exceptions import ValidationError
from eth_utils import (
    encode_hex,
    function_signature_to_4byte_selector
)
from ethereum.transactions import Transaction

import rlp
from web3 import Web3, HTTPProvider
from web3.utils.encoding import (
    hexstr_if_str,
    to_bytes,
    to_hex,
)
from web3.utils.transactions import get_buffered_gas_estimate
from web3.utils.validation import (
    validate_abi,
    validate_address,
)

from .exceptions import (
    SdkConfigurationError,
    SdkNotConfiguredError,
)
from .utils import load_keyfile

import logging
logger = logging.getLogger(__name__)

# ERC20 contract consts.
ERC20_TRANSFER_ABI_PREFIX = encode_hex(function_signature_to_4byte_selector('transfer(address, uint256)'))

# default gas configuration.
DEFAULT_GAS_PER_TX = 60000
DEFAULT_GAS_PRICE = 10 * 10 ** 9  # 10 Gwei

# default request retry configuration (linear backoff).
RETRY_ATTEMPTS = 3
RETRY_DELAY = 0.3


class TransactionStatus:
    """Transaction status enumerator."""
    UNKNOWN = 0
    PENDING = 1
    SUCCESS = 2
    FAIL = 3


class TransactionData(object):
    """Token transaction data holder"""
    from_address = None
    to_address = None
    ether_amount = 0
    token_amount = 0
    status = TransactionStatus.UNKNOWN
    num_confirmations = -1


class SDK(object):
    """
    This class is the primary interface to the ERC20 Token Python SDK.
    It maintains a connection context with an Ethereum JSON-RPC node and hides most of the specifics
    of dealing with Ethereum JSON-RPC API.
    """

    def __init__(self, keyfile='', password='', private_key='', provider='', provider_endpoint_uri='',
                 contract_address='', contract_abi={}):
        """Create a new instance of the Token SDK.

        The SDK needs a JSON-RPC provider, contract definitions and (optionally) a wallet private key.

        The user may pass either a provider or a provider endpoint URI, in which case a default
        :class:`web3:providers:HTTPProvider` will be created. If neither private_key nor keyfile+password
        are provided, the SDK can still be used in "anonymous" mode, with only the following functions available:
            - get_address_ether_balance
            - get_transaction_status
            - get_transaction_data
            - monitor_ether_transactions

        :param str private_key: a private key to initialize the wallet with. If either private key or keyfile
            are not provided, the wallet will not be initialized and methods needing the wallet will raise exception.

        :param str keyfile: the path to the keyfile to initialize the wallet with. You will also need to supply
            a password for this keyfile.

        :param str password: a password for the keyfile.

        :param provider: JSON-RPC provider to work with. If not given, a default `web3:providers:HTTPProvider`
            is used, inited with provider_endpoint_uri.
        :type provider: :class:`web3:providers:BaseProvider`

        :param str provider_endpoint_uri: a URI to use with a default HTTPProvider.

        :param str contract_address: the address of the token contract.

        :param list contract_abi: The contract ABI json.

        :returns: An instance of the SDK.
        :rtype: :class:`~erc20token.SDK`

        :raises: :class:`~erc20token.exceptions.SdkConfigurationError` if some of the configuration
            parameters are invalid.
        """

        if not provider and not provider_endpoint_uri:
            raise SdkConfigurationError('either provider or provider endpoint must be provided')

        try:
            validate_address(contract_address)
        except ValueError as ve:
            raise SdkConfigurationError('invalid token contract address: ' + str(ve))

        try:
            validate_abi(contract_abi)
        except Exception as e:
            raise SdkConfigurationError('invalid token contract abi: ' + str(e))

        if provider:
            self.web3 = Web3(provider)
        else:
            self.web3 = Web3(HTTPProvider(provider_endpoint_uri))
        if not self.web3.isConnected():
            raise SdkConfigurationError('cannot connect to provider endpoint')

        self.token_contract = self.web3.eth.contract(contract_address, abi=contract_abi)
        self.private_key = None
        self.address = None

        if keyfile:
            try:
                self.private_key = load_keyfile(keyfile, password)
            except Exception as e:
                raise SdkConfigurationError('cannot load keyfile: ' + str(e))
        elif private_key:
            self.private_key = private_key

        if self.private_key:
            try:
                private_key_bytes = hexstr_if_str(to_bytes, self.private_key)
                pk = keys.PrivateKey(private_key_bytes)
                self.address = self.web3.eth.defaultAccount = pk.public_key.to_checksum_address()
            except ValidationError as e:
                raise SdkConfigurationError('cannot load private key: ' + str(e))

            # init transaction manager
            self._tx_manager = TransactionManager(self.web3, self.private_key, self.address, self.token_contract)

        # monitoring filter manager
        self._filter_mgr = FilterManager(self.web3)

    def __del__(self):
        """The destructor is used to remove filter subscriptions, if any."""
        if hasattr(self, '_filter_mgr') and self._filter_mgr:
            self._filter_mgr.remove_filters()

    def get_address(self):
        """Get public address of the SDK wallet.
        The wallet is configured by a private key supplied during SDK initialization.

        :returns: public address of the wallet.
        :rtype: str

        :raises: :class:`~erc20token.exceptions.SdkConfigurationError`: if the SDK was not configured with a private key.
        """
        if not self.address:
            raise SdkNotConfiguredError('private key not configured')
        return self.address

    def get_ether_balance(self):
        """Get Ether balance of the SDK wallet.
        The wallet is configured by a private key supplied in during SDK initialization.

        :returns: : the balance in Ether of the internal wallet.
        :rtype: Decimal

        :raises: :class:`~erc20token.exceptions.SdkConfigurationError`: if the SDK was not configured with a private key.
        """
        if not self.address:
            raise SdkNotConfiguredError('private key not configured')
        return self.web3.fromWei(self.web3.eth.getBalance(self.address), 'ether')

    def get_token_balance(self):
        """Get token balance of the SDK wallet.
        The wallet is configured by a private key supplied in during SDK initialization.

        :returns: : the balance in tokens of the internal wallet.
        :rtype: Decimal

        :raises: :class:`~erc20token.exceptions.SdkConfigurationError`: if the SDK was not configured with a private key.
        """
        if not self.address:
            raise SdkNotConfiguredError('private key not configured')
        return self.web3.fromWei(self.token_contract.call().balanceOf(self.address), 'ether')

    def get_address_ether_balance(self, address):
        """Get Ether balance of a public address.

        :param: str address: a public address to query.

        :returns: the balance in Ether of the provided address.
        :rtype: Decimal

        :raises: ValueError: if the supplied address has a wrong format.
        """
        validate_address(address)
        return self.web3.fromWei(self.web3.eth.getBalance(address), 'ether')

    def get_address_token_balance(self, address):
        """Get token balance of a public address.

        :param: str address: a public address to query.

        :returns: : the balance in tokens of the provided address.
        :rtype: Decimal

        :raises: ValueError: if the supplied address has a wrong format.
        """
        validate_address(address)
        return self.web3.fromWei(self.token_contract.call().balanceOf(address), 'ether')

    def send_ether(self, address, amount):
        """Send Ether from my wallet to address.

        :param str address: the address to send Ether to.

        :param Decimal amount: the amount of Ether to transfer.

        :return: transaction id (hash)
        :rtype: str

        :raises: :class:`~erc20token.exceptions.SdkConfigurationError`: if the SDK was not configured with a private key.
        :raises: ValueError: if the amount is not positive.
        :raises: ValueError: if the address has a wrong format.
        :raises: ValueError: if the nonce is incorrect.
        :raises: ValueError: if insufficient funds for for gas * gas_price + value.
        """
        if not self.address:
            raise SdkNotConfiguredError('private key not configured')
        validate_address(address)
        if amount <= 0:
            raise ValueError('amount must be positive')
        return self._tx_manager.send_transaction(address, amount)

    def send_tokens(self, address, amount):
        """Send tokens from my wallet to address.

        :param str address: the address to send tokens to.

        :param Decimal amount: the amount of tokens to transfer.

        :returns: transaction id (hash)
        :rtype: str

        :raises: :class:`~erc20token.exceptions.SdkConfigurationError`: if the SDK was not configured with a private key.
        :raises: ValueError: if the amount is not positive.
        :raises: ValueError: if the address has a wrong format.
        :raises: ValueError: if the nonce is incorrect.
        :raises: ValueError: if insufficient funds for for gas * gas_price.
        """
        if not self.address:
            raise SdkNotConfiguredError('private key not configured')
        validate_address(address)
        if amount <= 0:
            raise ValueError('amount must be positive')
        hex_data = self.token_contract._encode_transaction_data('transfer', args=(address, self.web3.toWei(amount, 'ether')))
        data = hexstr_if_str(to_bytes, hex_data)
        return self._tx_manager.send_transaction(self.token_contract.address, 0, data)

    def get_transaction_status(self, tx_id):
        """Get the transaction status for the provided transaction id.

        :param str tx_id: transaction id (hash).

        :returns: transaction status.
        :rtype: :class:`~erc20token.TransactionStatus`
        """
        tx = self.web3.eth.getTransaction(tx_id)
        if not tx:
            return TransactionStatus.UNKNOWN
        return self._get_tx_status(tx)

    def get_transaction_data(self, tx_id):
        """Gets transaction data for the provided transaction id.

        :param str tx_id: transaction id (hash)
        :return: transaction data
        :rtype: :class:`~erc20token.TransactionData`
        """
        tx_data = TransactionData()
        tx = self.web3.eth.getTransaction(tx_id)
        if not tx:
            return tx_data
        tx_data.from_address = tx['from']
        tx_data.to_address = tx['to']
        tx_data.ether_amount = self.web3.fromWei(tx['value'], 'ether')
        tx_data.status = self._get_tx_status(tx)
        if not tx.get('blockNumber'):
            tx_data.num_confirmations = 0
        else:
            tx_block_number = int(tx['blockNumber'])
            cur_block_number = int(self.web3.eth.blockNumber)
            tx_data.num_confirmations = cur_block_number - tx_block_number + 1
        tx_input = tx.get('input')
        if tx_input and (tx_input.lower().startswith(ERC20_TRANSFER_ABI_PREFIX.lower())):
            to, amount = decode_abi(['uint256', 'uint256'], tx_input[len(ERC20_TRANSFER_ABI_PREFIX):])
            tx_data.to_address = to_hex(to)
            tx_data.token_amount = self.web3.fromWei(amount, 'ether')
        return tx_data

    def monitor_ether_transactions(self, callback_fn, from_address=None, to_address=None):
        """Monitors Ether transactions and calls back on transactions matching the supplied filter.

        :param callback_fn: the callback function with the signature `func(tx_id, status, from_address, to_address, amount)`

        :param str from_address: the transactions must originate from this address. If not provided,
            all addresses will match.

        :param str to_address: the transactions must be sent to this address. If not provided,
            all addresses will match.
        """
        filter_args = self._get_filter_args(from_address, to_address)

        def check_and_callback(tx, status):
            if tx.get('input') and not (tx['input'] == '0x' or tx['input'] == '0x0'):  # contract transaction, skip it
                return
            if ('from' in filter_args and tx['from'].lower() == filter_args['from'].lower() and
                    ('to' not in filter_args or tx['to'].lower() == filter_args['to'].lower()) or
                    ('to' in filter_args and tx['to'].lower() == filter_args['to'].lower())):
                callback_fn(tx['hash'], status, tx['from'], tx['to'], self.web3.fromWei(tx['value'], 'ether'))

        def pending_tx_callback_adapter_fn(tx_id):
            tx = self.web3.eth.getTransaction(tx_id)
            if not tx:  # probably invalid and removed from tx pool
                return
            check_and_callback(tx, TransactionStatus.PENDING)

        def new_block_callback_adapter_fn(block_id):
            block = self.web3.eth.getBlock(block_id, True)
            for tx in block['transactions']:
                check_and_callback(tx, TransactionStatus.SUCCESS)  # TODO: number of block confirmations

        # start monitoring pending and latest transactions
        self._filter_mgr.add_filter('pending', pending_tx_callback_adapter_fn)
        self._filter_mgr.add_filter('latest', new_block_callback_adapter_fn)

    def monitor_token_transactions(self, callback_fn, from_address=None, to_address=None):
        """Monitors token transactions and calls back on transactions matching the supplied filter.

        :param callback_fn: the callback function with the signature `func(tx_id, status, from_address, to_address, amount)`

        :param str from_address: the transactions must originate from this address. If not provided,
            all addresses will match.

        :param str to_address: the transactions must be sent to this address. If not provided,
            all addresses will match. Note that token transactions are always sent to the contract, and the real
            recipient is found in transaction data. This function will decode the data and return the correct
            recipient address.
        """
        filter_args = self._get_filter_args(from_address, to_address)

        def pending_tx_callback_adapter_fn(tx_id):
            tx = self.web3.eth.getTransaction(tx_id)
            if not tx:  # probably invalid and removed from tx pool
                return
            ok, tx_from, tx_to, amount = self._check_parse_contract_tx(tx, filter_args)
            if ok:
                callback_fn(tx['hash'], TransactionStatus.PENDING, tx_from, tx_to, amount)

        def new_block_callback_adapter_fn(block_id):
            block = self.web3.eth.getBlock(block_id, True)
            for tx in block['transactions']:
                ok, tx_from, tx_to, amount = self._check_parse_contract_tx(tx, filter_args)
                if ok:
                    status = self._get_tx_status(tx)
                    callback_fn(tx['hash'], status, tx_from, tx_to, amount)

        # start monitoring pending and latest transactions
        self._filter_mgr.add_filter('pending', pending_tx_callback_adapter_fn)
        self._filter_mgr.add_filter('latest', new_block_callback_adapter_fn)

    # helpers

    def _get_tx_status(self, tx):
        """Determines transaction status.

        :param dict tx: transaction object

        :returns: the status of this transaction.
        :rtype: :class:`~erc20token.TransactionStatus`
        """
        if not tx.get('blockNumber'):
            return TransactionStatus.PENDING

        # transaction is mined
        tx_receipt = self.web3.eth.getTransactionReceipt(tx['hash'])

        # Byzantium fork introduced a status field
        tx_status = tx_receipt.get('status')
        if tx_status == '0x1' or tx_status == 1:
            return TransactionStatus.SUCCESS
        if tx_status == '0x0' or tx_status == 0:
            return TransactionStatus.FAIL

        # pre-Byzantium, no status field
        # failed transaction usually consumes all the gas
        if tx_receipt.get('gasUsed') < tx.get('gas'):
            return TransactionStatus.SUCCESS
        # WARNING: there can be cases when gasUsed == gas for successful transactions!
        # We give our transactions extra gas, so it should not happen.
        return TransactionStatus.FAIL

    def _check_parse_contract_tx(self, tx, filter_args):
        """Parse contract transaction and check whether it matches the supplied filter.
        If the transaction matches the filter, the first returned value will be True, and the rest will be
        correctly filled. If there is no match, the first returned value is False and the rest are empty.

        :param dict tx: transaction object

        :param dict filter_args: a filter that contains fields 'to', 'from' or both.

        :returns: matching status, from address, to address, token amount
        :rtype: tuple
        """
        if not tx.get('to') or tx['to'].lower() != self.token_contract.address.lower():  # must be sent to our contract
            return False, '', '', 0
        tx_input = tx.get('input')
        if not tx_input or tx_input == '0x':  # not a contract transaction
            return False, '', '', 0
        if not tx_input.lower().startswith(ERC20_TRANSFER_ABI_PREFIX.lower()):
            # only interested in calls to 'transfer' method
            return False, '', '', 0

        to, amount = decode_abi(['uint256', 'uint256'], tx_input[len(ERC20_TRANSFER_ABI_PREFIX):])
        to = to_hex(to)
        amount = self.web3.fromWei(amount, 'ether')
        if ('from' in filter_args and tx['from'].lower() == filter_args['from'].lower() and
                ('to' not in filter_args or to.lower() == filter_args['to'].lower()) or
                ('to' in filter_args and to.lower() == filter_args['to'].lower())):
            return True, tx['from'], to, amount
        return False, '', '', 0

    @staticmethod
    def _get_filter_args(from_address, to_address):
        if not from_address and not to_address:
            raise ValueError('either from_address or to_address or both must be provided')
        filter_args = {}
        if from_address:
            validate_address(from_address)
            filter_args['from'] = from_address
        if to_address:
            validate_address(to_address)
            filter_args['to'] = to_address
        return filter_args


class TransactionManager(object):
    """TransactionManager handles sending of raw transactions.
    Due to the requirement that nonce number be continuous, we need to serialize concurrent transactions
    and centralize nonce calculation.
    """

    def __init__(self, web3, private_key, address, token_contract):
        self.web3 = web3
        self.private_key = private_key
        self.address = address
        self.token_contract = token_contract
        self.local_nonce = self.web3.eth.getTransactionCount(self.address)
        self.lock = threading.Lock()

        # initial gas estimations
        self.ether_tx_gas_estimate = self.estimate_ether_tx_gas() or DEFAULT_GAS_PER_TX
        self.token_tx_gas_estimate = self.estimate_token_tx_gas() or DEFAULT_GAS_PER_TX
        self.gas_price = self.web3.eth.gasPrice or DEFAULT_GAS_PRICE

    def send_transaction(self, address, amount, data=b''):
        """Send transaction with retry.
        Submitting a raw transaction can result in a nonce collision error. In this case, the submission is
        retried with a new nonce.

        :param str address: the target address.

        :param Decimal amount: the amount of Ether to send.

        :param data: binary data to put into transaction data field.

        :returns: transaction id (hash)
        :rtype: str
        """

        if data:  # token transaction
            gas_estimate = self.token_tx_gas_estimate
        else:
            gas_estimate = self.ether_tx_gas_estimate

        with self.lock:
            attempts = 0
            while True:
                try:
                    remote_nonce = self.web3.eth.getTransactionCount(self.address, 'pending')
                    nonce = max(self.local_nonce, remote_nonce)
                    tx = Transaction(
                        nonce=nonce,
                        gasprice=self.gas_price,
                        startgas=gas_estimate,
                        to=address,
                        value=self.web3.toWei(amount, 'ether'),
                        data=data,
                    ).sign(self.private_key)
                    raw_tx_hex = self.web3.toHex(rlp.encode(tx))
                    tx_id = self.web3.eth.sendRawTransaction(raw_tx_hex)
                    # send successful, increment nonce.
                    self.local_nonce = nonce + 1
                    return tx_id
                except ValueError as ve:
                    if 'message' in ve.args[0]:
                        err_msg = ve.args[0]['message']
                        if ('nonce too low' in err_msg
                            or 'another transaction with same nonce' in err_msg
                            or "the tx doesn't have the correct nonce" in err_msg) \
                                and attempts < RETRY_ATTEMPTS:
                            logging.warning('transaction nonce error, retrying')
                            attempts += 1
                            sleep(RETRY_DELAY)  # TODO: exponential backoff, configurable retry?
                            continue
                    raise

    def estimate_ether_tx_gas(self):
        sample_tx = {
            'to': self.address,
            'from': self.address,
            'value': 1
        }
        return get_buffered_gas_estimate(self.web3, sample_tx, gas_buffer=5000)

    def estimate_token_tx_gas(self):
        hex_data = self.token_contract._encode_transaction_data('transfer', args=(self.address, 1000))
        sample_tx = {
            'to': self.token_contract.address,
            'from': self.address,
            'value': 0,
            'data': hex_data
        }
        return get_buffered_gas_estimate(self.web3, sample_tx, gas_buffer=10000)


class FilterManager(object):
    """FilterManager encapsulates transaction filters management.
    Currently, its main purpose is to override the `web3.eth.filter._run` worker function that does not handle
    exceptions and crashes the polling thread whenever an exception occurs.
    """
    def __init__(self, web3):
        self.web3 = web3
        self.filters = {}
        super(FilterManager, self).__init__()

    def add_filter(self, filter_params,  *callbacks):
        """Setup a new filter or add a callback if the filter already exists.
        After registering of a new filter, its worker function is overriden with our custom one.

        :param filter_params: parameters to pass to `web3.eth.filter`

        :param callbacks: callback function to add

        :returns: filter_id
        :rtype: str
        """
        filter_key = hash(filter_params)
        if filter_key not in self.filters:
            new_filter = self.web3.eth.filter(filter_params)
            # WARNING: ugly hack to replace thread worker
            new_filter._Thread__target = self._run_filter(filter_params, new_filter)
            new_filter.callbacks.extend(callbacks)
            self.filters[filter_key] = new_filter
            new_filter.start()
            sleep(0)
        else:
            self.filters[filter_key].callbacks.extend(callbacks)
        return self.filters[filter_key].filter_id

    def _run_filter(self, filter_params, filtr):
        if filtr.stopped:
            raise ValueError("Cannot restart a Filter")
        filtr.running = True

        def _runner():
            """Our custom filter worker"""
            while filtr.running:
                try:
                    changes = self.web3.eth.getFilterChanges(filtr.filter_id)
                    if changes:
                        for entry in changes:
                            for callback_fn in filtr.callbacks:
                                if filtr.is_valid_entry(entry):
                                    callback_fn(filtr.format_entry(entry))
                    sleep(1)  # TODO: configurable?
                except ValueError as ve:
                    if 'message' in ve.args[0] and ve.args[0]['message'] == 'filter not found':
                        logging.warning('filter {} has expired, recreating'.format(filtr.filter_id))
                        new_filter = self.web3.eth.filter(filter_params)
                        filtr.filter_id = new_filter.filter_id
        return _runner

    def remove_filters(self):
        """Unregister our filters from the node. Not mandatory, as filters will time out anyway."""
        for key, filtr in self.filters.items():
            filtr.stop_watching(0.1)
            self.filters.pop(key, None)

