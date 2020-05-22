import os
import subprocess

from typing import List

ETCDCTL_PATH = "/opt/mesosphere/bin/etcdctl"
ETCD_ENDPOINTS = "127.0.0.1:2379"

CA_CERT = "/run/dcos/pki/CA/ca-bundle.crt"


def is_enterprise():
    return os.getenv('DCOS_ENTERPRISE', 'false').lower() == 'true'


class EtcdCtl():
    """ wraps etcdctl around related configurations
    """

    def __init__(self, cert_type="root") -> None:
        self._base_args = self._get_base_args(cert_type)

    def _get_base_args(self, cert_type) -> List[str]:
        args = ["sudo", ETCDCTL_PATH]
        if is_enterprise():
            args += ["--endpoints=https://{}".format(ETCD_ENDPOINTS)]
            args += [
                "--cert=/run/dcos/pki/tls/certs/etcd-client-{}.crt".format(cert_type),
                "--key=/run/dcos/pki/tls/private/etcd-client-{}.key".format(cert_type),
                "--cacert={}".format(CA_CERT),
            ]
        else:
            args += ["--endpoints=http://{}".format(ETCD_ENDPOINTS)]

        return args

    def run(self, cmd: List[str], check: bool = True,
            env: dict = {}) -> subprocess.CompletedProcess:
        process = subprocess.run(
            self._base_args.copy() + cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=check)

        return process
