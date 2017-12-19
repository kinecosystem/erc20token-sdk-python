# -*- coding: utf-8 -*

# Copyright (C) 2017 Kin Foundation

import json
import os
import sys

import logging
logger = logging.getLogger(__name__)


def create_keyfile(private_key, password, filename):
    """Creates a wallet keyfile.
    See https://github.com/ethereum/go-ethereum/wiki/Passphrase-protected-key-store-spec

    :param str private_key: private key

    :param str password: keyfile password

    :param str filename: keyfile path

    :raises: NotImplementedError: when using Python 3
    """
    if sys.version_info.major >= 3:
        raise NotImplementedError('keyfile creation is only supported in python2')
    from ethereum.tools import keys
    keyfile_json = keys.make_keystore_json(private_key.encode(), password, kdf='scrypt')
    try:
        oldumask = os.umask(0)
        fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(keyfile_json, f)
    except IOError as e:
        logger.exception(e)
    finally:
        os.umask(oldumask)


def load_keyfile(keyfile, password):
    """Loads a private key from the given keyfile.

    :param str keyfile: keyfile path

    :param str password: keyfile password

    :returns: private key
    :rtype: str

    :raises: NotImplementedError: when using Python 3
    :raises: IOError: if the file is not found
    :raises: ValueError: if the keyfile format is invalid
    """
    if sys.version_info.major >= 3:
        raise NotImplementedError('keyfile usage is only supported in python2')
    with open(keyfile, 'r') as f:
        keystore = json.load(f)
        from ethereum.tools import keys as keys
        if not keys.check_keystore_json(keystore):
            raise ValueError('invalid keyfile format')
        return keys.decode_keystore_json(keystore, password)

