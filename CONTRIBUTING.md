# Contributing

Thank you for your interest in the project. We look forward to your contribution. In order to make the process as fast 
and streamlined as possible, here is a set of guidelines we recommend you follow.

## Reporting Issues
First of all, please be sure to check our documentation and [issue archive](https://github.com/kinfoundation/erc20token-sdk-python/issues) 
to find out if your issue has already been addressed, or is currently being looked at.

To start a discussion around a bug or a feature, [open a new issue](https://github.com/kinfoundation/erc20token-sdk-python/issues/new). 
When opening an issue, please provide the following information:

- SDK version and Python version
- OS version
- The issue you are encountering including a stacktrace if applicable
- Steps or a code snippet to reproduce the issue

For feature requests it is encouraged to include sample code highlighting a use case for the new feature.

## Use Github Pull Requests

All potential code changes should be submitted as pull requests on Github. A pull request should only include 
commits directly applicable to its change (e.g. a pull request that adds a new feature should not include PEP8 changes in
an unrelated area of the code). Please check the following guidelines for submitting a new pull request.

- Ensure that nothing has been broken by your changes by running the test suite. You can do so by running 
`make test` in the project root. 
- Write clear, self-contained commits. Your commit message should be concise and describe the nature of the change.
- Rebase proactively. Your pull request should be up to date against the current master branch.
- Add tests. All non-trivial changes should include full test coverage. Make sure there are relevant tests to 
ensure the code you added continues to work as the project evolves.
- Add docs. This usually applies to new features rather than bug fixes, but new behavior should always be documented.
- Follow the coding style described below.
- Ask questions. If you are confused about something pertaining to the project, feel free to communicate with us.

### Code Style

Code *must* be compliant with [PEP 8](https://www.python.org/dev/peps/pep-0008/). Use the latest version of 
[PEP8](https://pypi.python.org/pypi/pep8) or [flake8](https://pypi.python.org/pypi/flake8) to catch issues.

Git commit messages should include [a summary and proper line wrapping](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)

## Development
If you are looking to contribute to this SDK, here are the steps to get you started.

1. Fork this project
2. Setup your Python [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs):
```bash
$ mkvirtualenv erc20-sdk-python
$ workon erc20-sdk-python
```
3. Setup `pip` and `npm` dependencies:
```bash
$ make init
```
4. Work on code
5. Test your code locally
```bash
$ make test
```
The `make test` flow is as follows:
- runs `testrpc` with predefined accounts pre-filled with Ether.
- runs `truffle deploy --reset` to compile and deploy your contract. This will aso add some tokens to the first account.
- runs `pytest` to test your code

6. Test your code with live testnet (Ropsten). This will also run an additional concurrency test.
```bash
$ make test-ropsten
```

