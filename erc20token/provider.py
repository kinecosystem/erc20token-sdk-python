# -*- coding: utf-8 -*

# Copyright (C) 2017 Kin Foundation

import backoff
import requests
from web3 import HTTPProvider
from web3.utils.compat import make_post_request


class RetryHTTPProvider(HTTPProvider):
    """RetryHTTPProvider is a custom HTTPProvider that retries failed http requests."""

    def __init__(self, endpoint_uri, request_kwargs=None):
        super(RetryHTTPProvider, self).__init__(endpoint_uri, request_kwargs)

    def make_request(self, method, params):
        """overrides the parent method to replace `make_post_request` with custom implementation"""
        request_data = self.encode_rpc_request(method, params)
        raw_response = self.retriable_post_request(request_data)  # instead of make_post_request
        response = self.decode_rpc_response(raw_response)
        return response

    @backoff.on_exception(
        lambda: backoff.expo(factor=0.2),
        requests.exceptions.RequestException,
        max_tries=4,
        giveup=lambda e: e.response is not None and 400 <= e.response.status_code < 500
    )
    def retriable_post_request(self, request_data):
        return make_post_request(
            self.endpoint_uri,
            request_data,
            **self.get_request_kwargs()
        )
