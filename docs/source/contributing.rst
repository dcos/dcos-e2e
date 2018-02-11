Contributing to DC/OS E2E
=========================

Contributions to this repository must pass tests and linting.

.. contents::
  :depth: 2

Install Contribution Dependencies
---------------------------------

Install dependencies in a virtual environment.

.. code:: sh

    pip install --process-dependency-links --editable .[dev]

Optionally install the following tools for linting and interacting with Travis CI:

.. code:: sh

    gem install travis --no-rdoc --no-ri

Spell checking requires ``enchant``.
This can be installed on macOS, for example, with `Homebrew <http://brew.sh>`__:

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

To fix some lint errors, run the following:

.. code:: sh

    make fix-lint

Tests for this package
----------------------

Tests for this package must be run on a host which is supported by DC/OS Docker.
See the `DC/OS Docker README <https://github.com/dcos/dcos-docker/blob/master/README.md>`__.

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

Rotating license keys
~~~~~~~~~~~~~~~~~~~~~

DC/OS Enterprise requires a license key.
Mesosphere uses license keys internally for testing, and these expire regularly.
A license key is encrypted and used by the Travis CI tests.

To update this link use the following command, after setting the ``LICENSE_KEY_CONTENTS`` environment variable.

This command will affect all builds and not just the current branch.

We do not use `encrypted secret files <https://docs.travis-ci.com/user/encrypting-files/#Caveat>`__ in case the contents are shown in the logs.

We do not add an encrypted environment variable to ``.travis.yml`` because the license is too large.

.. code:: sh

    travis env set --repo mesosphere/dcos-e2e LICENSE_KEY_CONTENTS $LICENSE_KEY_CONTENTS

Updating the DC/OS Enterprise build artifact link
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A private link to DC/OS Enterprise is used by Travis CI.

To update this link use the following command, after setting the ``EE_ARTIFACT_URL`` environment variable.

.. code:: sh

    travis encrypt --repo mesosphere/dcos-e2e EE_ARTIFACT_URL="$EE_ARTIFACT_URL" --add

Parallel builders
~~~~~~~~~~~~~~~~~

Travis CI has a maximum test run time of 50 minutes.
In order to avoid this and to see failures faster, we run multiple builds per commit.
We run almost one builder per test.
Some tests are grouped as they can run quickly.

New Backends
------------

Currently only DC/OS Docker is supported.
However, it is intended that a ``Cluster`` can take a number of backends.

To create a cluster backend to pass as the ``cluster_backend`` parameter to a ``Cluster``, create a ``ClusterManager`` and ``ClusterBackend`` in ``src/dcos_e2e/backends``.

To run tests against this backend, modify ``cluster_backend`` in ``tests/conftest.py`` to provide this backend.

Goals
-----

Avoid flakiness
~~~~~~~~~~~~~~~

For timeouts, err on the side of a much longer timeout than necessary.

Do not access the web while running tests.

Parrallelisable Tests
~~~~~~~~~~~~~~~~~~~~~

The tests in this repository and using this harness are slow.
This harness must not get in the way of parallelisation efforts.

Logging
~~~~~~~

End to end tests are notoriously difficult to get meaning from.
To help with this, an "excessive logging" policy is used here.

Robustness
~~~~~~~~~~

Narrowing down bugs from end to end tests is hard enough without dealing with the framework’s bugs.
This repository aims to maintain high standards in terms of coding quality and quality enforcement by CI is part of that.

Untied to a particular backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently only DC/OS Docker is supported.
However, it is intended that multiple backends can be supported.
See "New Backends" for details.

Release Process
---------------

This repository aims to work with DC/OS OSS and DC/OS Enterprise ``master`` branches.
These are moving targets.
For this reason, `CalVer <http://calver.org/>`__ is used as a date at which the repository is last known to have worked with DC/OS OSS and DC/OS Enterprise is the main versioning use.

The release process is as follows.

#. Choose a new version.

   This should be today’s date in the format ``YYYY.MM.DD.MICRO``.
   ``MICRO`` should refer to the number of releases created on this date, starting from ``0``.

   .. code:: sh

       export DCOS_E2E_RELEASE=2017.06.15.0

#. Create a release branch:

   .. code:: sh

       git fetch origin
       git checkout -b release-$DCOS_E2E_RELEASE origin/master

#. Add changes in the new release to ``CHANGELOG.rst``.

   Do not add a change note which says that this updates the tool to work with the latest version of DC/OS OSS or DC/OS Enterprise, as this is implied.
   If this is the only change, add an empty entry to the changelog.

#. Bump the version of the software.

   Change ``VERSION`` in ``setup.py``.

#. Commit and push changes.

   .. code:: sh

       git commit -am "Bump version"
       git push

#. Create a Pull Request to merge the ``release`` branch into ``master``.

#. Merge the ``release`` Pull Request once CI has passed.

#. Tag a release:

   Visit https://github.com/mesosphere/dcos-e2e/releases/new.
   Set the "Tag version" to the new version.
   Choose "master" as the target.
   Add the changes from the changelog to the release description.

Updating DC/OS Docker
---------------------

`DC/OS Docker <https://github.com/dcos/dcos-docker.git>`__ is vendored in this repository using ``git subtree``.
To update DC/OS Docker, use the following command:

.. code:: sh

    make update-dcos-docker
