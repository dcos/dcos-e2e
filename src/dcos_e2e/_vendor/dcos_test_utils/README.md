# dcos-test-utils

This module is the backend for the `dcos_api_session` object used as a test harness in the [DC/OS integration tests](http://github.com/dcos/dcos/tree/master/packages/dcos-integration-test/extra). More specifically, this module provides utilities that allow:
* Storing common URL elements repeated between requests to the same service
* Providing a DC/OS-authenticated API Client that can be wrapped and composed with API Mixins
* Helper methods for managing Marathon and other DC/OS services

## System Requirements
* python 3.5
* local SSH client at /usr/bin/ssh

### Using the library interactively
```
python3.5 -m venv env
. env/bin/activate
pip3 install -r requirements.txt
python setup.py develop
```

## Running Tests with tox
Simply run `tox` and the following will be executed:
* flake8 for style errors
* pytest for unit tests

Note: these can be triggered individually by supplying the `-e` option to `tox`
