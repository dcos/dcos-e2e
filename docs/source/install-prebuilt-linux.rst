CLI on Linux with Pre-built Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One way to install the CLI on Linux is with a pre-built package.

.. version-prompt:: bash

   # Install dcos-docker
   curl -L -O /usr/local/bin/dcos-docker https://github.com/dcos/dcos-e2e/releases/download/|release|/dcos-docker && \
   chmod +x /usr/local/bin/dcos-docker
   # Install dcos-vagrant
   curl -L -O /usr/local/bin/dcos-vagrant https://github.com/dcos/dcos-e2e/releases/download/|release|/dcos-vagrant && \
   chmod +x /usr/local/bin/dcos-vagrant
   # Install dcos-aws
   curl -L -O /usr/local/bin/dcos-aws https://github.com/dcos/dcos-e2e/releases/download/|release|/dcos-aws && \
   chmod +x /usr/local/bin/dcos-aws
