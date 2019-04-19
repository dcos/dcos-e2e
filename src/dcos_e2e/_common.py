"""
Common utilities for end to end tests.
"""

import logging
import subprocess
from subprocess import PIPE, STDOUT, CompletedProcess, Popen
from typing import Dict, List, Optional, Union

LOGGER = logging.getLogger(__name__)


def _safe_decode(output_bytes: bytes) -> str:
    """
    Decode a bytestring to Unicode with a safe fallback.
    """
    try:
        return output_bytes.decode(
            encoding='utf-8',
            errors='strict',
        )
    except UnicodeDecodeError:
        return output_bytes.decode(
            encoding='ascii',
            errors='backslashreplace',
        )


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
    """
    process_stdout = PIPE if pipe_output else None
    process_stderr = PIPE if pipe_output else None

    # It is hard to log output of both stdout and stderr live unless we
    # combine them.
    # See http://stackoverflow.com/a/18423003.
    if log_output_live:
        process_stderr = STDOUT

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
                    log_message = _safe_decode(line.rstrip())
                    LOGGER.debug(log_message)
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

            # Attempt to give the subprocess(es) a chance to terminate.
            process.terminate()
            try:
                process.wait(1)
            except subprocess.TimeoutExpired:
                # If the process cannot terminate cleanly, we just kill it.
                process.kill()
            raise
        if stderr:
            if process.returncode == 0:
                log = LOGGER.warning
                log(repr(args))
            else:
                log = LOGGER.error
            for line in stderr.rstrip().split(b'\n'):
                log_message = _safe_decode(line.rstrip())
                log(log_message)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=process.returncode,
                cmd=args,
                output=stdout,
                stderr=stderr,
            )
    return CompletedProcess(args, process.returncode, stdout, stderr)
