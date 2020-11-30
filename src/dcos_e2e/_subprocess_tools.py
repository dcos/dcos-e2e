"""
Utilities for running subprocesses.
"""

import logging
import subprocess
import time
from subprocess import CompletedProcess
from typing import Callable, Dict, List, Optional, Union

import sarge

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


class _LineLogger:
    """
    A logger which logs full lines.
    """

    def __init__(self, logger: Callable[[str], None]) -> None:
        self._buffer = b''
        self._logger = logger

    def log(self, data: bytes) -> None:
        self._buffer += data

        lines = self._buffer.split(b'\n')
        self._buffer = lines.pop()

        for line in lines:
            self._logger(_safe_decode(line))

    def flush(self) -> None:
        if self._buffer:
            self._logger(_safe_decode(self._buffer))
            self._buffer = b''


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
        log_output_live: If `True`, log output live.
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
    stdout_list = []  # type: List[bytes]
    stderr_list = []  # type: List[bytes]
    stdout_logger = _LineLogger(LOGGER.debug)
    stderr_logger = _LineLogger(LOGGER.warning)

    def _read_output(process: sarge.Pipeline, block: bool) -> None:
        stdout_line = process.stdout.read(block=block)
        stderr_line = process.stderr.read(block=block)
        if stdout_line:
            stdout_list.append(stdout_line)
            if log_output_live:
                stdout_logger.log(stdout_line)
        if stderr_line:
            stderr_list.append(stderr_line)
            if log_output_live:
                stderr_logger.log(stderr_line)

    try:
        if pipe_output:
            process = sarge.capture_both(args, cwd=cwd, env=env, async_=True)
            while all(
                command.returncode is None for command in process.commands
            ):
                _read_output(process=process, block=False)
                process.poll_all()
                time.sleep(0.05)

            # block on final read to ensure all data read.
            _read_output(process=process, block=True)
        else:
            process = sarge.run(args, cwd=cwd, env=env, async_=True)

        stdout_logger.flush()
        stderr_logger.flush()
        # stderr/stdout are not readable anymore which usually means
        # that the child process has exited. However, the child
        # process has not been wait()ed for yet, i.e. it has not yet
        # been reaped. That is, its exit status is unknown. Read its
        # exit status
        process.wait()
    except Exception:  # pragma: no cover pylint: disable=broad-except
        for popen_process in process.processes:
            # We clean up if there is an error while getting the output.
            # This may not happen while running tests so we ignore coverage.

            # Attempt to give the subprocess(es) a chance to terminate.
            popen_process.terminate()
            try:
                popen_process.wait(1)
            except subprocess.TimeoutExpired:
                # If the process cannot terminate cleanly, we just kill it.
                popen_process.kill()
            raise

    stdout = b''.join(stdout_list) if pipe_output else None
    stderr = b''.join(stderr_list) if pipe_output else None
    if process.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=process.returncode,
            cmd=args,
            output=stdout,
            stderr=stderr,
        )
    return CompletedProcess(args, process.returncode, stdout, stderr)
