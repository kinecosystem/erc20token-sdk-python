#!/usr/bin/env bash

truffle deploy --reset > truffle.log 2>&1
grep -Po 'contract deployed at \K(.*)$$' truffle.log > token_contract_address.txt
