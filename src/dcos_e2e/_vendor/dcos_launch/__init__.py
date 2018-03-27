from .. import dcos_launch
from ..dcos_launch import acs_engine as ___vendorize__0
dcos_launch.acs_engine = ___vendorize__0
from .. import dcos_launch
from ..dcos_launch import arm as ___vendorize__0
dcos_launch.arm = ___vendorize__0
from .. import dcos_launch
from ..dcos_launch import aws as ___vendorize__0
dcos_launch.aws = ___vendorize__0
from .. import dcos_launch
from ..dcos_launch import gcp as ___vendorize__0
dcos_launch.gcp = ___vendorize__0
from .. import dcos_launch
from ..dcos_launch import onprem as ___vendorize__0
dcos_launch.onprem = ___vendorize__0
from .. import dcos_launch
from ..dcos_launch import util as ___vendorize__0
dcos_launch.util = ___vendorize__0

VERSION = '0.1.0'


def get_launcher(config, env=None):
    """Returns the correct class of launcher from a validated launch config dict
    """
    platform = config['platform']
    provider = config['provider']
    if platform == 'aws':
        if provider == 'aws':
            return dcos_launch.aws.DcosCloudformationLauncher(config, env=env)
        if provider == 'onprem':
            return dcos_launch.aws.OnPremLauncher(config, env=env)
    if platform == 'azure':
        if provider == 'azure':
            return dcos_launch.arm.AzureResourceGroupLauncher(config, env=env)
        if provider == 'acs-engine':
            return dcos_launch.acs_engine.ACSEngineLauncher(config, env=env)
    if platform == 'gcp':
        return dcos_launch.gcp.OnPremLauncher(config, env=env)
    raise dcos_launch.util.LauncherError('UnsupportedAction', 'Launch platform not supported: {}'.format(platform))
