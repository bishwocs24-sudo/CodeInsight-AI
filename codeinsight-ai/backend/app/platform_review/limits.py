import os
import signal
import subprocess
import tempfile
from pathlib import Path


class ProcessFailure(RuntimeError):
    pass


def bounded_process(args, *, timeout, cwd=None, memory=None, extra_env=None):
    """Run trusted tooling with bounded output, process lifetime and environment."""
    with tempfile.TemporaryDirectory(prefix="codeguard-tool-") as directory:
        out = Path(directory) / "stdout"
        err = Path(directory) / "stderr"
        env = {"PATH": os.environ.get("PATH", os.defpath), "HOME": directory, "LANG": "C.UTF-8"}
        env.update(extra_env or {})
        limits = ["prlimit", "--fsize=4000000:4000000", "--core=0:0"]
        if memory:
            limits.extend([f"--as={memory}:{memory}", f"--cpu={timeout}:{timeout + 1}"])
            env["SEMGREP_SEND_METRICS"] = "off"
        try:
            with out.open("wb") as stdout, err.open("wb") as stderr:
                process = subprocess.Popen(
                    [*limits, "--", *args], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, start_new_session=True,
                )
                try:
                    code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired as exc:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
                    raise ProcessFailure("Tool timed out") from exc
        except OSError as exc:
            raise ProcessFailure("Tool unavailable") from exc
        if code == 127 and err.read_bytes().startswith(b"prlimit:"):
            raise ProcessFailure("Tool unavailable")
        return code, out.read_bytes(), err.read_bytes()
