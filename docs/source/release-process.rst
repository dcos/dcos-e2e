Release Process
===============

Outcomes
--------


Prerequisites
-------------

* `Homebrew`_ or `Linuxbrew`_.
* ``git``.

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

#. Commit and push changes.

   .. code:: sh

       git commit -am "Bump version to $DCOS_E2E_RELEASE"
       git push

#. Create a Pull Request to merge the ``release`` branch into ``master``.

#. Merge the ``release`` Pull Request once CI has passed.

#. Tag a release:

   Visit https://github.com/mesosphere/dcos-e2e/releases/new.
   Set the "Tag version" to the new version.
   Choose "master" as the target.
   Add the changes from the changelog to the release description.

.. _Homebrew: https://brew.sh/
.. _Linuxbrew: http://linuxbrew.sh/
