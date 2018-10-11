""" Logging configuration for the DC/OS testing utilities

Certain libraries used in this repository have excessively verbose output on
the debug level (as python logging does not natively have a trace level).
Invoking this module will effectively lower the level of the messages from
the targed modules by one level.
"""
import logging

LOGGING_FORMAT = '[%(asctime)s|%(name)s|%(levelname)s]: %(message)s'

MODULE_BROWN_LIST = [
    'botocore',
    'boto3']


def setup(log_level_str: str, noisy_modules: list=None):
    """ Handles the builtin python log levels and adds level below
    debug (trace) which dampened modules will log debug at

    Args:
        log_level_str: user-provided string to set the log-level
        noisy_modules: any additional modules that should have their level increased
    """
    if log_level_str == 'CRITICAL':
        log_level = logging.CRITICAL
    elif log_level_str == 'ERROR':
        log_level = logging.ERROR
    elif log_level_str == 'WARNING':
        log_level = logging.WARNING
    elif log_level_str == 'INFO':
        log_level = logging.INFO
    elif log_level_str == 'DEBUG' or log_level_str == 'TRACE':
        log_level = logging.DEBUG
    else:
        raise ValueError('{} is not a valid log level'.format(log_level_str))
    logging.basicConfig(format=LOGGING_FORMAT, level=log_level)
    if log_level_str in ('TRACE', 'CRITICAL'):
        # trace logging is supposd to show all; no need to raise log level
        # critical logging is the highest level so its meaningless to raise more
        return
    # now dampen the loud loggers
    module_list = MODULE_BROWN_LIST
    if noisy_modules is not None:
        module_list.extend(noisy_modules)
    for module in module_list:
        logging.getLogger(module).setLevel(log_level + 10)
