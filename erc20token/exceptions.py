# -*- coding: utf-8 -*

# Copyright (C) 2017 Kin Foundation


class SdkError(Exception):
    """Base class for all SDK errors."""


class SdkConfigurationError(SdkError):
    """Cannot create SDK instance due to misconfiguration"""
    pass


class SdkNotConfiguredError(SdkError):
    """Cannot call some SDK functions that need extra configuration details"""
    pass

