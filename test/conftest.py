import pytest


def pytest_addoption(parser):
    parser.addoption("--ropsten", action="store_true", default=False, help="whether testing on Ropsten instead of local testrpc")


@pytest.fixture(scope='session')
def ropsten(request):
    return request.config.getoption("--ropsten")
