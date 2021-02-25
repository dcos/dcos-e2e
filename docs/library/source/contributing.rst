Contributing
============

Contributions to this repository must pass tests and linting.

.. contents::
  :depth: 2

.. _install-contribution-dependencies:

Install Contribution Dependencies
---------------------------------

.. include:: install-python-build-dependencies.rst

Install dependencies in a virtual environment.

If you are not in a virtualenv, you may have to use ``sudo`` before the following command, or ``--user`` after ``install``.

.. prompt:: bash
   :substitutions:

    pip3 install --editable '.[dev]'

Optionally install the following tools for linting and interacting with Travis CI:

.. prompt:: bash
   :substitutions:

    gem install travis --no-rdoc --no-ri

Spell checking requires ``enchant``.
This can be installed on macOS, for example, with `Homebrew`_:

.. prompt:: bash
   :substitutions:

    brew install enchant

and on Ubuntu with ``apt``:

.. prompt:: bash
   :substitutions:

    apt install -y enchant

Linting Bash requires `shellcheck`_:
This can be installed on macOS, for example, with `Homebrew`_:

.. prompt:: bash
   :substitutions:

    brew install shellcheck

and on Ubuntu with ``apt``:

.. prompt:: bash
   :substitutions:

    apt-get install -y shellcheck

Linting
-------

:ref:`install-contribution-dependencies`.

Run lint tools:

.. prompt:: bash
   :substitutions:

    make lint

These can be run in parallel with:

.. prompt:: bash
   :substitutions:

   make lint --jobs --output-sync=target

To fix some lint errors, run the following:

.. prompt:: bash
   :substitutions:

    make fix-lint

Tests for this package
----------------------

Some tests require the Docker backend and some tests require the AWS backend.
See the :doc:`Docker backend documentation <docker-backend>` for details of what is needed for the Docker backend.
See the :doc:`AWS backend documentation <aws-backend>` for details of what is needed for the AWS backend.

To run the full test suite, set environment variables for DC/OS Enterprise installer URLs:

.. prompt:: bash
   :substitutions:

   export EE_MASTER_INSTALLER_URL=https://...
   export EE_1_9_INSTALLER_URL=https://...
   export EE_1_10_INSTALLER_URL=https://...
   export EE_1_11_INSTALLER_URL=https://...

Download dependencies which are used by the tests:

.. prompt:: bash
   :substitutions:

   python admin/download_installers.py

A license key is required for some tests:

.. prompt:: bash
   :substitutions:

    cp /path/to/license-key.txt /tmp/license-key.txt

Run ``pytest``:

.. prompt:: bash
   :substitutions:

    pytest

To run the tests concurrently, use `pytest-xdist <https://github.com/pytest-dev/pytest-xdist>`__.
For example:

.. prompt:: bash
   :substitutions:

    pytest -n 2

Documentation
-------------

Run the following commands to build and open the documentation:

.. prompt:: bash
   :substitutions:

    make docs
    make open-docs

Reviews
-------

Ask Adam Dangoor if you are unsure who to ask for help from.

CI
--

Linting and some tests are run on GitHub Actions and Travis CI.
See ``.github/workflows`` and ``.travis.yml`` for details.

Most of the CLI functionality is not covered by automated tests.
Changes should take this into consideration.

Rotating license keys
~~~~~~~~~~~~~~~~~~~~~

DC/OS Enterprise requires a license key.
D2iQ uses license keys internally for testing, and these expire regularly.
A license key is encrypted and used by the Travis CI tests.

To update this link use the following command, after setting the ``LICENSE_KEY_CONTENTS`` environment variable.

This command will affect all builds and not just the current branch.

We do not use `encrypted secret files <https://docs.travis-ci.com/user/encrypting-files/>`__ in case the contents are shown in the logs.

We do not add an encrypted environment variable to ``.travis.yml`` because the license is too large.

.. prompt:: bash
   :substitutions:

    travis env set --repo |github-owner|/|github-repository| LICENSE_KEY_CONTENTS $LICENSE_KEY_CONTENTS

Updating the DC/OS Enterprise build installer links
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Private links to DC/OS Enterprise installers are used by Travis CI.

To update these links use the following commands, after setting the following environment variables:

* ``EE_MASTER_INSTALLER_URL``
* ``EE_1_9_INSTALLER_URL``
* ``EE_1_10_INSTALLER_URL``
* ``EE_1_11_INSTALLER_URL``
* ``EE_1_12_INSTALLER_URL``

.. prompt:: bash
   :substitutions:

    travis env set --repo |github-owner|/|github-repository| EE_MASTER_INSTALLER_URL $EE_MASTER_INSTALLER_URL
    travis env set --repo |github-owner|/|github-repository| EE_1_9_INSTALLER_URL $EE_1_9_INSTALLER_URL
    travis env set --repo |github-owner|/|github-repository| EE_1_10_INSTALLER_URL $EE_1_10_INSTALLER_URL
    travis env set --repo |github-owner|/|github-repository| EE_1_11_INSTALLER_URL $EE_1_11_INSTALLER_URL
    travis env set --repo |github-owner|/|github-repository| EE_1_12_INSTALLER_URL $EE_1_12_INSTALLER_URL

Updating the Amazon Web Services credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Private credentials for Amazon Web Services are used by Travis CI.

To update the credentials use the following commands, after setting the following environment variables:

* ``AWS_ACCESS_KEY_ID``
* ``AWS_SECRET_ACCESS_KEY``

.. prompt:: bash
   :substitutions:

    travis env set --repo |github-owner|/|github-repository| AWS_ACCESS_KEY_ID $AWS_ACCESS_KEY_ID
    travis env set --repo |github-owner|/|github-repository| AWS_SECRET_ACCESS_KEY $AWS_SECRET_ACCESS_KEY

Parallel builders
~~~~~~~~~~~~~~~~~

Travis CI has a maximum test run time of 50 minutes.
In order to avoid this and to see failures faster, we run multiple builds per commit.
We run almost one builder per test.
Some tests are grouped as they can run quickly.


Goals
-----

Avoid flakiness
~~~~~~~~~~~~~~~

For timeouts, err on the side of a much longer timeout than necessary.

Do not access the web while running tests.

Parallelizable Tests
~~~~~~~~~~~~~~~~~~~~

The tests in this repository and using this harness are slow.
This harness must not get in the way of parallelization efforts.

Logging
~~~~~~~

End to end tests are notoriously difficult to get meaning from.
To help with this, an "excessive logging" policy is used here.

Robustness
~~~~~~~~~~

Narrowing down bugs from end to end tests is hard enough without dealing with the framework’s bugs.
This repository aims to maintain high standards in terms of coding quality and quality enforcement by CI is part of that.

Version Policy
--------------

This repository aims to work with DC/OS OSS and DC/OS Enterprise ``master`` branches.
These are moving targets.
For this reason, `CalVer <https://calver.org/>`__ is used as a date at which the repository is last known to have worked with DC/OS OSS and DC/OS Enterprise is the main versioning use.

Release Process
---------------

See :doc:`release-process`.

Updating vendored packages
--------------------------

Various repositories, such as `DC/OS Test Utils <https://github.com/dcos/dcos-test-utils>`__ and `DC/OS Launch <https://github.com/dcos/dcos-launch>`__ are vendored in this repository.
To update DC/OS Test Utils or DC/OS Launch:

Update the SHAs in ``admin/update_vendored_packages.py``.

The following creates a commit with changes to the vendored packages:

.. prompt:: bash
   :substitutions:

   admin/update_vendored_packages.sh

Upstream Blockers
-----------------

This codebase includes workarounds for various issues.
These include, at least:

* ``make fix-lint`` uses multiple rounds of reformatting to work around https://github.com/myint/autoflake/issues/8.

* The Homebrew recipe we use downgrades ``pip`` to work around https://github.com/pypa/pip/issues/6222.

* We disable the ``pylint`` issue ``no-value-for-parameter`` to avoid https://github.com/PyCQA/pylint/issues/207.

* We disable ``yapf`` in multiple places to avoid https://github.com/google/yapf/issues/524.

* We ignore a type error to avoid https://github.com/python/mypy/issues/5135.



.. _Homebrew: https://brew.sh/
.. _Linuxbrew: http://linuxbrew.sh/
.. _shellcheck: https://www.shellcheck.net
