Enterprise
==========

Enterprise is different...

.. code:: python

    import subprocess
    import uuid
    from pathlib import Path

    from dcos_e2e.backends import Docker
    from dcos_e2e.cluster import Cluster
    from passlib.hash import sha512_crypt

    def test_ee_example():

        ee_artifact = Path('/tmp/dcos_generate_config.ee.sh')
        license_key_contents = Path('/tmp/license-key.txt').read_text()

        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())

        # DC/OS Enterprise clusters require various configuration variables which
        # are not allowed or required by DC/OS OSS clusters.
        extra_config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        with Cluster(cluster_backend=Docker()) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=ee_artifact,
                extra_config=extra_config,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )
