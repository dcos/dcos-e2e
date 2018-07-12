"""DC/OS Launch

Usage:
  dcos-launch create [-L LEVEL -c PATH -i PATH]
  dcos-launch wait [-L LEVEL -i PATH]
  dcos-launch describe [-L LEVEL -i PATH]
  dcos-launch pytest [-L LEVEL -i PATH -e LIST] [--] [<pytest_extras>]...
  dcos-launch delete [-L LEVEL -i PATH]

Commands:
  create    Reads the file given by --config-path, creates the cluster
              described therein and finally dumps a JSON file to the path
              given in --info-path which can then be used with the wait,
              describe, pytest, and delete calls.
  wait      Block until the cluster is up and running.
  describe  Return additional information about the composition of the cluster.
  pytest    Runs integration test suite on cluster. Can optionally supply
              options and arguments to pytest
  delete    Destroying the provided cluster deployment.

Options:
  -c PATH --config-path=PATH
            Path for config to create cluster from [default: config.yaml].
  -i PATH --info-path=PATH
            JSON file output by create and consumed by wait, describe,
            and delete [default: cluster_info.json].
  -e LIST --env=LIST
            Specifies a comma-delimited list of environment variables to be
            passed from the local environment into the test environment.
  -L LEVEL --log-level=LEVEL
            One of: critical, error, warning, info, debug, and trace
            [default: debug].
"""
import os
import sys

from .. import dcos_launch
from .. import dcos_launch
from ..dcos_launch import config as ___vendorize__0
dcos_launch.config = ___vendorize__0
from ..dcos_launch import util
from ..dcos_test_utils import logger
from docopt import docopt


def do_main(args):
    logger.setup(args['--log-level'].upper(), noisy_modules=['googleapiclient', 'oauth2client'])

    if args['create']:
        config = dcos_launch.config.get_validated_config_from_path(args['--config-path'])
        info_path = args['--info-path']
        if os.path.exists(info_path):
            raise dcos_launch.util.LauncherError(
                'InputConflict',  '{} already exists! Delete this or specify a '
                'different cluster info path with the -i option'.format(info_path))
        launcher = dcos_launch.get_launcher(config)
        cluster_info = launcher.create()
        util.write_json(info_path, cluster_info)
        create_exception = getattr(launcher, 'create_exception', None)
        if create_exception:
            raise create_exception
        return 0

    try:
        info = util.load_json(args['--info-path'])
    except FileNotFoundError as ex:
        raise dcos_launch.util.LauncherError('MissingInfoJSON', None) from ex

    launcher = dcos_launch.get_launcher(info)

    if args['wait']:
        launcher.wait()
        launcher.install_dcos()
        print('Cluster is ready!')
        return 0

    if args['describe']:
        print(util.json_prettyprint(launcher.describe()))
        return 0

    if args['pytest']:
        var_list = list()
        if args['--env'] is not None:
            if '=' in args['--env']:
                # User is attempting to do an assignment with the option
                raise dcos_launch.util.LauncherError(
                    'OptionError', "The '--env' option can only pass through environment variables "
                    "from the current environment. Set variables according to the shell being used.")
            var_list = args['--env'].split(',')
            missing = [v for v in var_list if v not in os.environ]
            if len(missing) > 0:
                raise dcos_launch.util.LauncherError(
                    'MissingInput', 'Environment variable arguments have been indicated '
                    'but not set: {}'.format(repr(missing)))
        env_dict = {e: os.environ[e] for e in var_list}
        return launcher.test(args['<pytest_extras>'], env_dict)

    if args['delete']:
        launcher.delete()
        return 0


def main(argv=None):
    args = docopt(__doc__, argv=argv, version='dcos-launch {}'.format(dcos_launch.VERSION))

    try:
        return do_main(args)
    except dcos_launch.util.LauncherError as ex:
        print('DC/OS Launch encountered an error!')
        print(repr(ex))
        return 1


if __name__ == '__main__':
    sys.exit(main())
