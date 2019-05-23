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

Reboot
~~~~~~

DC/OS nodes cannot be rebooted.
The cluster cannot survive a system reboot.

Resources UI
~~~~~~~~~~~~

The DC/OS web UI Resources tab shows resources available to each DC/OS node.
On a cluster with a Docker backend, resources are not specific to one node.
That means, if the cluster has 16 GB memory available in total, the web UI will show that each node has 16 GB memory available.

Marathon-LB
~~~~~~~~~~~

Network configuration options vary by kernel version.
If you see the following when installing Marathon-LB,
change the Marathon-LB ``sysctl-params`` configuration value:

.. code:: console

   sysctl: cannot stat /proc/sys/net/ipv4/tcp_tw_reuse: No such file or directory
   sysctl: cannot stat /proc/sys/net/ipv4/tcp_max_syn_backlog: No such file or directory
   sysctl: cannot stat /proc/sys/net/ipv4/tcp_max_tw_buckets: No such file or directory
   sysctl: cannot stat /proc/sys/net/ipv4/tcp_max_orphans: No such file or directory

Remove the relevant ``sysctl-params`` values.
This may leave:

.. code:: console

    net.ipv4.tcp_fin_timeout=30 net.core.somaxconn=10000
