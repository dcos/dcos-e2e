Using DC/OS Enterprise
======================

DC/OS Enterprise requires various configuration variables which are not allowed or required by open source DC/OS.

The following example shows how to use DC/OS Enterprise with DC/OS E2E.

.. code:: python

    from pathlib import Path

    from dcos_e2e.backends import Docker
    from dcos_e2e.cluster import Cluster
    from passlib.hash import sha512_crypt

    ee_artifact = Path('/tmp/dcos_generate_config.ee.sh')
    license_key_contents = Path('/tmp/license-key.txt').read_text()

    superuser_username = 'my_username'
    superuser_password = 'my_password'

    extra_config = {
        'superuser_username': superuser_username,
        'superuser_password_hash': sha512_crypt.hash(superuser_password),
        'fault_domain_enabled': False,
        'license_key_contents': license_key_contents,
    }

    with Cluster(cluster_backend=Docker()) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=ee_artifact,
            base_config={
                **cluster.base_config,
                **extra_config,
            },
        )
        cluster.wait_for_dcos_ee(
            superuser_username=superuser_username,
            superuser_password=superuser_password,
        )

        cluster.run_integration_tests(
            env={
                'DCOS_LOGIN_UNAME': superuser_username,
                'DCOS_LOGIN_PW': superuser_password,
            }
            pytest_command=['pytest', '-k', 'tls'],
        )
