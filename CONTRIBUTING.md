# Contributing to DC/OS End to End tests

Contributions to this repository must pass tests and linting.
Linting is run on Travis CI.
Tests are currently not run on CI.

## Install Contribution Dependencies

Install dependencies in a virtual environment.

```sh
pip install --editable .[dev]
```

```sh
gem install travis --no-rdoc --no-ri
```

## Linting

Run lint tools:

```sh
make lint
```

To fix some lint errors, run the following:

```sh
make fix-lint
```

## Tests for this package

Tests for this package must be run in a suitable environment.
See "Test Environment" in the `README`.

Run `pytest`:

```sh
pytest
```

To run the tests concurrently, use [pytest-xdist](https://github.com/pytest-dev/pytest-xdist).
For example:

```sh
pytest -n 2
```

## Reviews

Ask Adam Dangoor if you are unsure who to ask for help from.

## CI

Linting and some tests are run on Travis CI.
See `.travis.yml` for details on the limitations.
To check if a new change works on CI, unfortunately it is necessary to change `.travis.yml` to run the desired tests.
