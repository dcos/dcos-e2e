"""
Common utilities for end to end tests.
"""

import logging
from subprocess import (
    PIPE,
    STDOUT,
    CalledProcessError,
    CompletedProcess,
    Popen,
)
from typing import List, Optional, Union

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


def run_subprocess(
    args: List[str],
    log_output_live: bool,
    cwd: Optional[Union[bytes, str]] = None
) -> CompletedProcess:
    """
    Run a command in a subprocess.

    Args:
        args: See `subprocess.run`.
        log_output_live: If `True`, log output live. If `True`, stderr is
            merged into stdout in the return value.
        cwd: See `subprocess.run`.

    Returns:
        See `subprocess.run`.

    Raises:
        CalledProcessError: See `subprocess.run`.
    """
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
        stdout=PIPE,
        stderr=process_stderr,
    ) as process:
        try:
            if log_output_live:
                stdout = b''
                stderr = b''
                for line in process.stdout:
                    LOGGER.debug(line)
                    stdout += line
                # Without this, `.poll()` will return None on some
                # systems.
                # See https://stackoverflow.com/a/33563376.
                process.communicate()
            else:
                stdout, stderr = process.communicate()
        except:  # noqa: B001 pragma: no cover
            # We clean up if there is an error while getting the output.
            # This may not happen while running tests so we ignore coverage.
            process.kill()
            process.wait()
            raise
        retcode = process.poll()
        if retcode > 0:
            LOGGER.info(str(stderr))
            raise CalledProcessError(
                retcode, args, output=stdout, stderr=stderr
            )
    return CompletedProcess(args, retcode, stdout, stderr)
