from ..dcos_launch import dcos_engine, arm, aws, gcp, terraform, util

VERSION = '0.1.0'


def get_launcher(config, env=None):
    """Returns the correct class of launcher from a validated launch config dict
    """
    platform = config['platform']
    provider = config['provider']
    if platform == 'aws':
        if provider == 'aws':
            return aws.DcosCloudformationLauncher(config, env=env)
        if provider == 'onprem':
            return aws.OnPremLauncher(config, env=env)
        if provider == 'terraform':
            return terraform.AwsLauncher(config, env=env)
    if platform == 'azure':
        if provider == 'azure':
            return arm.AzureResourceGroupLauncher(config, env=env)
        if provider == 'dcos-engine':
            return dcos_engine.DcosEngineLauncher(config, env=env)
        if provider == 'terraform':
            return terraform.AzureLauncher(config, env=env)
    if platform == 'gcp':
        if provider == 'terraform':
            return terraform.GcpLauncher(config, env=env)
        if provider == 'onprem':
            return gcp.OnPremLauncher(config, env=env)
    raise util.LauncherError('UnsupportedAction', 'Launch platform not supported: {}'.format(platform))
