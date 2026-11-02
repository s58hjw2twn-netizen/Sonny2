"""Bounded local subprocess adapter. NOT a sandbox or isolation proof.

Caller must establish isolation independently before using this module.
"""
from dataclasses import dataclass
import subprocess
import threading
from .voice_whisper_command import WhisperCommand

@dataclass(frozen=True)
class WhisperRunResult:
    returncode: int
    stdout: str
    stderr: str

def run_prepared_whisper(command: WhisperCommand, *, approved: bool = False,
                         isolation_verified: bool = False,
                         timeout_seconds: int = 30,
                         max_output_bytes: int = 65536) -> WhisperRunResult:
    # A caller-supplied boolean cannot prove process isolation. Do not execute
    # an untrusted speech engine on the host until a sandbox-owned executor
    # replaces this legacy API. This gate intentionally fails closed.
    raise PermissionError("direct host Whisper execution disabled; sandbox executor required")
    if not isinstance(command, WhisperCommand) or len(command.argv) != 6:
        raise ValueError("expected prepared Whisper command")
    if command.argv[1] != "-m" or command.argv[3] != "-f" or command.argv[5] != "-nt":
        raise ValueError("unexpected Whisper arguments")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 120:
        raise ValueError("timeout out of bounds")
    if type(max_output_bytes) is not int or not 1 <= max_output_bytes <= 65536:
        raise ValueError("output limit out of bounds")

    process = subprocess.Popen(
        list(command.argv), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=False,
    )
    chunks = [bytearray(), bytearray()]
    overflow = threading.Event()
    def read_bounded(stream, buffer):
        try:
            while True:
                data = stream.read(4096)
                if not data:
                    break
                remaining = max_output_bytes - len(buffer)
                buffer.extend(data[:max(0, remaining)])
                if len(data) > remaining:
                    overflow.set()
                    process.kill()
                    break
        finally:
            stream.close()

    workers = [
        threading.Thread(target=read_bounded, args=(process.stdout, chunks[0]), daemon=True),
        threading.Thread(target=read_bounded, args=(process.stderr, chunks[1]), daemon=True),
    ]
    for worker in workers:
        worker.start()
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait()
        raise TimeoutError("Whisper execution timed out") from exc
    finally:
        for worker in workers:
            worker.join(timeout=2)
    if overflow.is_set():
        raise ValueError("Whisper output exceeded limit")
    if any(worker.is_alive() for worker in workers):
        raise RuntimeError("Whisper output reader did not terminate")
    return WhisperRunResult(
        process.returncode,
        chunks[0].decode("utf-8", errors="replace"),
        chunks[1].decode("utf-8", errors="replace"),
    )
