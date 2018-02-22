Release Process
===============

Outcomes
--------

* A new ``git`` tag available to install.
* An updated `Homebrew`_ recipe.
* Python 3.5+.

Prerequisites
-------------

* `Homebrew`_ or `Linuxbrew`_.
* ``git``.

Performing a Release
--------------------

#. Clone DC/OS E2E:

   .. code:: sh

      git clone git@github.com:mesosphere/dcos-e2e.git

# Create a virtual environment:

    .. code:: sh

       cd dcos-e2e
       pip install --editable .[dev]

#. Choose a new version:

   This should be today’s date in the format ``YYYY.MM.DD.MICRO``.
   ``MICRO`` should refer to the number of releases created on this date, starting from ``0``.

   .. code:: sh

       export DCOS_E2E_RELEASE=2017.06.15.0

#. Create a release branch:

   .. code:: sh

       git fetch origin
       git checkout -b release-$DCOS_E2E_RELEASE origin/master

#. Update Homebrew

   .. code:: sh

      make update-homebrew

#. Change ``CHANGELOG.rst`` title.



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
