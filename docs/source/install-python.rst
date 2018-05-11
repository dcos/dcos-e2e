Library and CLI with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the CLI has been installed with Homebrew, you do not need to install the library to use the CLI.

Requires Python 3.5.2+.
To avoid interfering with your system's Python, we recommend using a `virtualenv <https://virtualenv.pypa.io/en/stable/>`_.

Check the Python version:

.. code:: sh

   python3 --version

On Fedora, install Python development requirements:

.. code:: sh

   sudo dnf install -y git python3-devel

On Ubuntu, install Python development requirements:

.. code:: sh

   apt install -y gcc python3-dev

Optionally replace ``master`` with a particular version of DC/OS E2E.
The latest release is |release|.
See `available versions <https://github.com/mesosphere/dcos-e2e/tags>`_.

If you are not in a virtualenv, you may have to use ``sudo`` before the following command, or ``--user`` after ``install``.

.. code:: sh

    pip3 install git+https://github.com/mesosphere/dcos-e2e.git@master

Run :ref:`dcos-docker-doctor` to make sure that your system is ready to go for the Docker backend:

.. code-block:: console

   $ dcos-docker doctor
