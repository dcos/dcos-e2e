Limitations
-----------

Docker does not represent a real DC/OS environment with complete accuracy.
This section describes the currently known differences between the Docker backend and a real DC/OS environment.

SELinux
~~~~~~~

Tests inherit the host’s environment.
Any tests that rely on SELinux being available require it be available on the host.

Storage
~~~~~~~

Docker does not support storage features expected in a real DC/OS environment.
