# -*- coding: utf-8 -*

# Copyright (C) 2017 Kin Foundation

import json
import sys


def create_keyfile(private_key, password, filename):
    """Creates a wallet keyfile.
    See https://github.com/ethereum/go-ethereum/wiki/Passphrase-protected-key-store-spec

    :param str private_key: private key

    :param str password: keyfile password

    :param str filename: keyfile path

    :raises: NotImplementedError: when using Python 2
    """
    if sys.version_info.major >= 3:
        raise NotImplementedError('keyfile creation is only supported in python2')
    from ethereum.tools import keys
    keyfile_json = keys.make_keystore_json(private_key.encode(), password, kdf='scrypt')
    with open(filename, 'w+') as f:
        json.dump(keyfile_json, f)


def load_keyfile(keyfile, password):
    """Loads a private key from the given keyfile.

    :param str keyfile: keyfile path

    :param str password: keyfile password

    :returns: private key
    :rtype: str

    :raises: NotImplementedError: when using Python 2
    :raises: IOError: if the file is not found
    :raises: ValueError: if the keyfile format is invalid
    """
    if sys.version_info.major >= 3:
        raise NotImplementedError('keyfile usage is only supported in python2')
    with open(keyfile, 'r') as f:
        keystore = json.load(f)
        from ethereum.tools import keys as ekeys
        if not ekeys.check_keystore_json(keystore):
            raise ValueError('invalid keyfile format')
        return ekeys.decode_keystore_json(keystore, password)

