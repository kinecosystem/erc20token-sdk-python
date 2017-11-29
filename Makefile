
# default target does nothing
.DEFAULT_GOAL: default
default: ;

export PATH := ./test/truffle_env/node_modules/.bin:$(PATH)

init:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	cd ./test/truffle_env && npm install
.PHONY: init

test-ropsten:
	python -m pytest -v -rs --ropsten --cov=erc20token -s -x test
.PHONY: test

test: truffle
	python -m pytest -v -rs --cov=erc20token -s -x test
.PHONY: test

truffle: testrpc truffle-clean
	cd ./test/truffle_env && npm run-script truffle
.PHONY: truffle

truffle-clean:
	cd ./test/truffle_env && rm -f *.log token_contract_address.txt

testrpc:
	cd ./test/truffle_env && npm run-script testrpc
.PHONY: testrpc

clean: truffle-clean
	rm -f .coverage
	find . -name \*.pyc -delete
.PHONY: clean
