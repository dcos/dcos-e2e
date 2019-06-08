With Python (``pip``)
~~~~~~~~~~~~~~~~~~~~~

Requires Python 3.5.2+.
To avoid interfering with your system's Python, we recommend using a `virtualenv <https://virtualenv.pypa.io/en/stable/>`_.

Check the Python version:

.. This has been tested by using:
.. $ docker run -it fedora bash

.. substitution-prompt:: bash

   python3 --version

On Fedora, install Python development requirements:

.. substitution-prompt:: bash

   dnf install -y git python3-devel

On Ubuntu, install Python development requirements:

.. Note: This is duplicated in the library installation section.
.. This has been tested by using:
.. $ docker run -it vcatechnology/linux-mint bash
.. and
.. $ docker run -it ubuntu bash

.. substitution-prompt:: bash

   apt update -y && \
   apt install -y software-properties-common && \
   apt upgrade -y python-apt && \
   add-apt-repository -y ppa:deadsnakes/ppa && \
   apt update -y && \
   apt upgrade -y gcc python3-dev python3.6-dev libffi-dev libssl-dev git python3-pip

If you are not in a virtualenv, you may have to use ``sudo`` before the following command, or ``--user`` after ``install``.

.. substitution-prompt:: bash

    pip3 install --upgrade git+https://github.com/|github-owner|/|github-repository|.git@|release|
