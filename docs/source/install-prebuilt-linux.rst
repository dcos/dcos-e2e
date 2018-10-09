CLI on Linux with Pre-built Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One way to install the CLI on Linux is with a pre-built package.

.. smart-prompt:: bash

   # Install dcos-docker
   curl --fail -L https://github.com/|github-owner|/|github-repository|/releases/download/|release|/dcos-docker /usr/local/bin/dcos-docker && \
   chmod +x /usr/local/bin/dcos-docker
   # Install dcos-vagrant
   curl --fail -L https://github.com/|github-owner|/|github-repository|/releases/download/|release|/dcos-vagrant /usr/local/bin/dcos-vagrant && \
   chmod +x /usr/local/bin/dcos-vagrant
   # Install dcos-aws
   curl --fail -L https://github.com/|github-owner|/|github-repository|/releases/download/|release|/dcos-aws /usr/local/bin/dcos-aws && \
   chmod +x /usr/local/bin/dcos-aws
