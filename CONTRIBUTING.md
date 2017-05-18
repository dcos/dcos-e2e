# Contributing to DC/OS End to End tests

Contributions to this repository must pass tests and linting.
Linting is run on Travis CI.
Tests are currently not run on CI.

<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Install Contribution Dependencies](#install-contribution-dependencies)
- [Linting](#linting)
- [Tests for this package](#tests-for-this-package)
- [Documentation](#documentation)
- [Reviews](#reviews)
- [CI](#ci)
- [Goals](#goals)
  - [Avoid flakiness](#avoid-flakiness)
  - [Parrallelisable Tests](#parrallelisable-tests)
  - [Logging](#logging)
  - [Robustness](#robustness)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

## Install Contribution Dependencies

Install dependencies in a virtual environment.

```sh
pip install --editable .[dev]
```

Optionally install the following lint tools:

```sh
gem install travis --no-rdoc --no-ri
```

```sh
npm install
```

Spell checking requires `enchant`.
This can be installed on macOS, for example, with [Homebrew](http://brew.sh):

```sh
brew install enchant
```

and on Ubuntu with `apt`:

```sh
apt-get install -y enchant
```

To contribute documentation, install the following tool to create tables of content.

```sh
npm install -g doctoc
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

To run only the lint tools which require Python, run the following:

```sh
make lint-python-only
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

## Documentation

Run the following command to update the tables of contents:

```sh
doctoc README.md CONTRIBUTING.md --github --title "**Table of Contents**"
```

## Reviews

Ask Adam Dangoor if you are unsure who to ask for help from.

## CI

Linting and some tests are run on Travis CI.
See `.travis.yml` for details on the limitations.
To check if a new change works on CI, unfortunately it is necessary to change `.travis.yml` to run the desired tests.

## Goals

### Avoid flakiness

For timeouts, err on the side of a much longer timeout than necessary.

Do not access the web while running tests.

### Parrallelisable Tests

The tests in this repository and using this harness are slow. This harness must not get in the way of parallelisation efforts.

### Logging

End to end tests are notoriously difficult to get meaning from. To help with this, an "excessive logging" policy is used here.

### Robustness

Narrowing down bugs from end to end tests is hard enough without dealing with the framework's bugs.
This repository aims to maintain high standards in terms of coding quality and quality enforcement by CI is part of that.
