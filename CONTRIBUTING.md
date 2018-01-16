# Contributing to DC/OS End to End tests

Contributions to this repository must pass tests and linting.

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
- [New Backends](#new-backends)
- [Goals](#goals)
  - [Avoid flakiness](#avoid-flakiness)
  - [Parrallelisable Tests](#parrallelisable-tests)
  - [Logging](#logging)
  - [Robustness](#robustness)
  - [Untied to a particular backend](#untied-to-a-particular-backend)
- [Release Process](#release-process)
- [Updating DC/OS Docker](#updating-dcos-docker)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

## Install Contribution Dependencies

Install dependencies in a virtual environment.

```sh
pip install --process-dependency-links --editable .[dev]
```

Optionally install the following tools for linting and interacting with Travis CI:

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

Tests for this package must be run on a host which is supported by DC/OS Docker.
See the [DC/OS Docker README](https://github.com/dcos/dcos-docker/blob/master/README.md).

Download dependencies which are used by the tests:

```sh
make download-artifacts
```

or, to additionally download a DC/OS Enterprise artifact, run the following:

```sh
make EE_ARTIFACT_URL=<http://...> download-artifacts
```

The DC/OS Enterprise artifact is required for some tests.

A license key is required for some tests:

```sh
cp /path/to/license-key.txt /tmp/license-key.txt
```

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
make toc
```

## Reviews

Ask Adam Dangoor if you are unsure who to ask for help from.

## CI

Linting and some tests are run on Travis CI.
See `.travis.yml` for details on the limitations.
To check if a new change works on CI, unfortunately it is necessary to change `.travis.yml` to run the desired tests.

### Rotating license keys

DC/OS Enterprise requires a license key.
Mesosphere uses license keys internally for testing, and these expire regularly.
A license key is encrypted and used by the Travis CI tests.

To update the license key, put a file with the contents to use at `license-key.txt` in the root directory of a clone of this repository.
Do not share this file or push it to GitHub.
Encrypt this file and push the encrypted file to GitHub.

```sh
travis encrypt-file license-key.txt --add --force
git add license-key.txt.enc .travis.yml
git commit -m 'Update license key'
git push
```

### Updating the DC/OS Enterprise build artifact link

A private link to DC/OS Enterprise is used by Travis CI.

To update this link use the following command, after setting the `EE_ARTIFACT_URL` environment variable.

```sh
travis encrypt --repo mesosphere/dcos-e2e EE_ARTIFACT_URL="$EE_ARTIFACT_URL" --add
```

### Parallel builders

Travis CI has a maximum test run time of 50 minutes.
In order to avoid this and to see failures faster, we run multiple builds per commit.
We run almost one builder per test.
Some tests are grouped as they can run quickly.

## New Backends

Currently only DC/OS Docker is supported.
However, it is intended that a `Cluster` can take a number of backends.

To create a cluster backend to pass as the `cluster_backend` parameter to a `Cluster`, create a `ClusterManager` and `ClusterBackend` in `src/dcos_e2e/backends`.

To run tests against this backend, modify `cluster_backend` in `tests/conftest.py` to provide this backend.

## Goals

### Avoid flakiness

For timeouts, err on the side of a much longer timeout than necessary.

Do not access the web while running tests.

### Parrallelisable Tests

The tests in this repository and using this harness are slow.
This harness must not get in the way of parallelisation efforts.

### Logging

End to end tests are notoriously difficult to get meaning from.
To help with this, an "excessive logging" policy is used here.

### Robustness

Narrowing down bugs from end to end tests is hard enough without dealing with the framework's bugs.
This repository aims to maintain high standards in terms of coding quality and quality enforcement by CI is part of that.

### Untied to a particular backend

Currently only DC/OS Docker is supported.
However, it is intended that multiple backends can be supported.
See "New Backends" for details.

## Release Process

This repository aims to work with DC/OS OSS and DC/OS Enterprise `master` branches.
These are moving targets.
For this reason, [CalVer](http://calver.org/) is used as a date at which the repository is last known to have worked with DC/OS OSS and DC/OS Enterprise is the main versioning use.

The release process is as follows.

1. Choose a new version.

This should be today's date in the format `YYYY.MM.DD.MICRO`.
`MICRO` should refer to the number of releases created on this date, starting from `0`.

```sh
export DCOS_E2E_RELEASE=2017.06.15.0
```

2. Create a release branch:

```sh
git fetch origin
git checkout -b release-$DCOS_E2E_RELEASE origin/master
```

3. Add changes in the new release to `CHANGELOG.md`.

Do not add a change note which says that this updates the tool to work with the latest version of DC/OS OSS or DC/OS Enterprise, as this is implied.
If this is the only change, add an empty entry to the changelog.

4. Update the changelog Table of Contents.

```sh
make toc
```

5. Bump the version of the software.

Change `VERSION` in `setup.py`.

6. Commit and push changes.

```sh
git commit -am "Bump version"
git push
```

6. Create a Pull Request to merge the `release` branch into `master`.

7. Merge the `release` Pull Request once CI has passed.

8. Tag a release.

Visit <https://github.com/mesosphere/dcos-e2e/releases/new>.
Set the "Tag version" to the new version.
Choose "master" as the target.
Add the changes from the changelog to the release description.

## Updating DC/OS Docker

[DC/OS Docker](https://github.com/dcos/dcos-docker.git) is vendored in this repository using `git subtree`.
To update DC/OS Docker, use the following command:

```sh
make update-dcos-docker
```
