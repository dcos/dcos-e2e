Contributing
============

Contributions to this repository must pass tests and linting.

.. contents::
  :depth: 2

Install Contribution Dependencies
---------------------------------

Install dependencies in a virtual environment.

.. code:: sh

    pip install --editable .[dev]

Optionally install the following tools for linting and interacting with Travis CI:

.. code:: sh

    gem install travis --no-rdoc --no-ri

Spell checking requires ``enchant``.
This can be installed on macOS, for example, with `Homebrew <https://brew.sh>`__:

.. code:: sh

    brew install enchant

and on Ubuntu with ``apt``:

.. code:: sh

    apt-get install -y enchant

Linting
-------

Run lint tools:

.. code:: sh

    make lint

These can be run in parallel with:

.. code:: sh

   make lint --jobs --output-sync=target

To fix some lint errors, run the following:

.. code:: sh

    make fix-lint

Tests for this package
----------------------

Some tests require the Docker backend and some tests require the AWS backend.
See the :doc:`Docker backend documentation <docker-backend>` for details of what is needed for the Docker backend.
See the :doc:`AWS backend documentation <aws-backend>` for details of what is needed for the AWS backend.

Download dependencies which are used by the tests:

.. code:: sh

    make download-artifacts

or, to additionally download a DC/OS Enterprise artifact, run the following:

.. code:: sh

    make EE_ARTIFACT_URL=<http://...> download-artifacts

The DC/OS Enterprise artifact is required for some tests.

A license key is required for some tests:

.. code:: sh

    cp /path/to/license-key.txt /tmp/license-key.txt

Run ``pytest``:

.. code:: sh

    pytest

To run the tests concurrently, use `pytest-xdist <https://github.com/pytest-dev/pytest-xdist>`__.
For example:

.. code:: sh

    pytest -n 2

Documentation
-------------

Run the following commands to build and open the documentation:

.. code:: sh

    make docs
    make open-docs

Reviews
-------

Ask Adam Dangoor if you are unsure who to ask for help from.

CI
--

Linting and some tests are run on Travis CI.
See ``.travis.yml`` for details on the limitations.
To check if a new change works on CI, unfortunately it is necessary to change ``.travis.yml`` to run the desired tests.

Most of the CLI functionality is not covered by automated tests.
Changes should take this into consideration.

Rotating license keys
~~~~~~~~~~~~~~~~~~~~~

DC/OS Enterprise requires a license key.
Mesosphere uses license keys internally for testing, and these expire regularly.
A license key is encrypted and used by the Travis CI tests.

To update this link use the following command, after setting the ``LICENSE_KEY_CONTENTS`` environment variable.

This command will affect all builds and not just the current branch.

We do not use `encrypted secret files <https://docs.travis-ci.com/user/encrypting-files/>`__ in case the contents are shown in the logs.

We do not add an encrypted environment variable to ``.travis.yml`` because the license is too large.

.. code:: sh

    travis env set --repo mesosphere/dcos-e2e LICENSE_KEY_CONTENTS $LICENSE_KEY_CONTENTS

Updating the DC/OS Enterprise build artifact links
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Private links to DC/OS Enterprise artifacts are used by Travis CI.

To update these links use the following commands, after setting the following environment variables:

* ``EE_MASTER_ARTIFACT_URL``
* ``EE_1_9_ARTIFACT_URL``
* ``EE_1_10_ARTIFACT_URL``
* ``EE_1_11_ARTIFACT_URL``

.. code:: sh

    travis env set --repo mesosphere/dcos-e2e EE_MASTER_ARTIFACT_URL $EE_MASTER_ARTIFACT_URL
    travis env set --repo mesosphere/dcos-e2e EE_1_9_ARTIFACT_URL $EE_1_9_ARTIFACT_URL
    travis env set --repo mesosphere/dcos-e2e EE_1_10_ARTIFACT_URL $EE_1_10_ARTIFACT_URL
    travis env set --repo mesosphere/dcos-e2e EE_1_11_ARTIFACT_URL $EE_1_11_ARTIFACT_URL

Updating the Amazon Web Services credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Private credentials for Amazon Web Services are used by Travis CI.

To update the credentials use the following commands, after setting the following environment variables:

* ``AWS_ACCESS_KEY_ID``
* ``AWS_SECRET_ACCESS_KEY``

.. code:: sh

    travis env set --repo mesosphere/dcos-e2e AWS_ACCESS_KEY_ID $AWS_ACCESS_KEY_ID
    travis env set --repo mesosphere/dcos-e2e AWS_SECRET_ACCESS_KEY $AWS_SECRET_ACCESS_KEY

Currently credentials are taken from the OneLogin Secure Notes note ``dcos-e2e integration testing AWS credentials``.

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
For this reason, `CalVer <http://calver.org/>`__ is used as a date at which the repository is last known to have worked with DC/OS OSS and DC/OS Enterprise is the main versioning use.

Release Process
---------------

See :doc:`release-process`.

Updating DC/OS Test Utils and DC/OS Launch
------------------------------------------

`DC/OS Test Utils <https://github.com/dcos/dcos-test-utils>`__ and `DC/OS Launch <https://github.com/dcos/dcos-launch>`__ are vendored in this repository.
To update DC/OS Test Utils or DC/OS Launch:

Update the SHAs in ``admin/update_vendored_packages.py``.

The following creates a commit with changes to the vendored packages:

.. code:: sh

   admin/update_vendored_packages.sh

Redirect DC/OS Launch package resources
---------------------------------------

In order discover its package resources after an update of the vendored DC/OS Launch, all references to ``dcos_launch`` must be replaced with ``dcos_e2e._vendor.dcos_launch`` in the following files.

* :file:`dcos_e2e/_vendor/dcos_launch/config.py`
* :file:`dcos_e2e/_vendor/dcos_launch/onprem.py`
* :file:`dcos_e2e/_vendor/dcos_launch/platform/aws.py`

The progress on automating this procedure is tracked in :issue:`DCOS-21895`.

Testing the Homebrew Recipe
----------------------------

Install `Homebrew`_ or `Linuxbrew`_.

.. code:: sh

   brew install dcosdocker.rb
   brew audit dcosdocker
   brew test dcosdocker


.. _Homebrew: https://brew.sh/
.. _Linuxbrew: http://linuxbrew.sh/
