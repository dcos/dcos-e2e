Installing |project|
--------------------

Requires Python 3.5.2+.
To avoid interfering with your system's Python, we recommend using a `virtualenv <https://virtualenv.pypa.io/en/stable/>`_.

Check the Python version:

.. substitution-prompt:: bash

   python3 --version

On Fedora, install Python development requirements:

.. substitution-prompt:: bash

   sudo dnf install -y git python3-devel

On Ubuntu, install Python development requirements:

.. substitution-prompt:: bash

   apt install -y gcc python3-dev

If you are not in a virtualenv, you may have to use ``sudo`` before the following command, or ``--user`` after ``install``.

.. substitution-prompt:: bash

    pip3 install --upgrade git+https://github.com/|github-owner|/|github-repository|.git@|release|

Uninstall
~~~~~~~~~

To uninstall |project|, run the following command:

.. substitution-prompt:: bash

   pip3 uninstall -y dcos-e2e
