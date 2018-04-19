"""
Common utilities for end to end tests.
"""

import logging
import subprocess
from subprocess import PIPE, STDOUT, CompletedProcess, Popen
from typing import Dict, List, Optional, Union


def get_logger(name: str) -> logging.Logger:
    """
    Return a customized logger that is able to log on DEBUG level.

    Args:
        name: Name of the logger. Setting this to ``__name__`` will log
            the path to the file where the logger has been created.

    Returns:
        See :py:class:`logging.Logger`.
    """
    # This gets the root logger with a ``logging.lastResort``
    # StreamHandler that logs on WARNING level.
    logger = logging.getLogger(name)

    # Do this if a logger is called for the first time
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        # Add a new StreamHandler that logs on DEBUG level in order
        # to override the ``logging.lastResort`` handler.
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)

        # Take control of the logging format
        formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)-8s %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


LOGGER = get_logger(__name__)


def run_subprocess(
    args: List[str],
    log_output_live: bool,
    cwd: Optional[Union[bytes, str]] = None,
    env: Optional[Dict[str, str]] = None,
    pipe_output: bool = True,
) -> CompletedProcess:
    """
    Run a command in a subprocess.

    Args:
        args: See :py:func:`subprocess.run`.
        log_output_live: If `True`, log output live. If `True`, stderr is
            merged into stdout in the return value.
        cwd: See :py:func:`subprocess.run`.
        env: See :py:func:`subprocess.run`.
        pipe_output: If ``True``, pipes are opened to stdout and stderr.
            This means that the values of stdout and stderr will be in
            the returned ``subprocess.CompletedProcess`` and optionally
            sent to a logger, given ``log_output_live``.
            If ``False``, no output is sent to a logger and the values are
            not returned.

    Returns:
        See :py:func:`subprocess.run`.

    Raises:
        subprocess.CalledProcessError: See :py:func:`subprocess.run`.
        Exception: An exception was raised in getting the output from the call.
        ValueError: ``log_output_live`` is ``True`` and ``pipe_output`` is
            ``False``.
    """
    if log_output_live and not pipe_output:
        raise ValueError(
            '`log_output_live` cannot be `True` if `pipe_output` is `False`.',
        )

    process_stdout = PIPE if pipe_output else None
    # It is hard to log output of both stdout and stderr live unless we
    # combine them.
    # See http://stackoverflow.com/a/18423003.
    if log_output_live:
        process_stderr = STDOUT
    else:
        process_stderr = PIPE

    with Popen(
        args=args,
        cwd=cwd,
        stdout=process_stdout,
        stderr=process_stderr,
        env=env,
    ) as process:
        try:
            if log_output_live:
                stdout = b''
                stderr = b''
                for line in process.stdout:
                    LOGGER.debug(
                        line.rstrip().decode('ascii', 'backslashreplace'),
                    )
                    stdout += line
                # stderr/stdout are not readable anymore which usually means
                # that the child process has exited. However, the child
                # process has not been wait()ed for yet, i.e. it has not yet
                # been reaped. That is, its exit status is unknown. Read its
                # exit status.
                process.wait()
            else:
                stdout, stderr = process.communicate()
        except Exception:  # pragma: no cover
            # We clean up if there is an error while getting the output.
            # This may not happen while running tests so we ignore coverage.
            process.kill()
            process.wait()
            raise
        if stderr:
            if process.returncode == 0:
                log = LOGGER.warning
                log(repr(args))
            else:
                log = LOGGER.error
            for line in stderr.rstrip().split(b'\n'):
                log(line.rstrip().decode('ascii', 'backslashreplace'))
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                args,
                output=stdout,
                stderr=stderr,
            )
    return CompletedProcess(args, process.returncode, stdout, stderr)
