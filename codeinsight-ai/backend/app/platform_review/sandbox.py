import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.core.config import get_settings
from app.platform_review.limits import ProcessFailure, bounded_process


def verify_python(source: str, tests: str) -> dict:
    """Run explicitly submitted Python tests in a disposable offline container."""
    settings = get_settings()
    if not settings.sandbox_enabled:
        return {"status": "disabled"}
    docker_env = {"DOCKER_HOST": settings.sandbox_docker_host} if settings.sandbox_docker_host else {}
    try:
        code, output, _ = bounded_process(
            ["docker", "info", "--format", "{{json .}}"], timeout=5, extra_env=docker_env,
        )
        info = json.loads(output) if code == 0 else {}
        if not all(info.get(key) is True for key in ("MemoryLimit", "SwapLimit", "CpuCfsQuota", "PidsLimit")):
            return {"status": "isolation_unavailable"}
        if not any(option.startswith("name=seccomp") and "unconfined" not in option
                   for option in (info.get("SecurityOptions") or [])):
            return {"status": "isolation_unavailable"}
    except (ProcessFailure, ValueError):
        return {"status": "unavailable"}
    name = f"codeguard-{uuid4().hex}"
    with TemporaryDirectory(prefix="codeguard-tests-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        (root / "submission.py").write_text(source, encoding="utf-8")
        (root / "test_submission.py").write_text(tests, encoding="utf-8")
        command = [
            "docker", "run", "--rm", "--pull=never", "--name", name,
            "--network=none", "--read-only", "--cap-drop=ALL", "--init",
            "--security-opt=no-new-privileges", "--user=65534:65534",
            "--memory=128m", "--memory-swap=128m", "--cpus=0.5", "--pids-limit=32",
            "--ulimit", "nofile=128:128", "--ulimit", "fsize=1048576:1048576",
            "--log-driver=none", "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
            "--mount", f"type=bind,src={root},dst=/workspace,readonly",
            "--workdir", "/workspace", "--entrypoint", "/usr/local/bin/python",
            settings.sandbox_image, "-B", "-m", "unittest", "-v", "test_submission",
        ]
        try:
            code, _, _ = bounded_process(command, timeout=25, extra_env=docker_env)
            if code in {125, 126, 127}:
                return {"status": "unavailable"}
            return {"status": "passed" if code == 0 else "failed", "exit_code": code}
        except ProcessFailure as exc:
            return {"status": "timed_out" if str(exc) == "Tool timed out" else "unavailable"}
        finally:
            try:
                bounded_process(["docker", "rm", "-f", name], timeout=5, extra_env=docker_env)
            except ProcessFailure:
                pass
