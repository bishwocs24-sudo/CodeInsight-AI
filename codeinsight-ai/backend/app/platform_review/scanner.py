import hashlib
import json
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from app.core.config import get_settings
from app.platform_review.evidence import Source, finding
from app.platform_review.limits import ProcessFailure, bounded_process

RULES = Path(__file__).with_name("semgrep_rules.yml").resolve()
RULE_VERSION = hashlib.sha256(RULES.read_bytes()).hexdigest()
SEMGREP_VERSION = "1.186.0"  # Keep in sync with requirements-scanner.txt.
SEVERITIES = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}


def scan(sources: list[Source]):
    if not sources:
        return [], "no_supported_files"
    binary = get_settings().semgrep_binary
    if "/" in binary:
        binary = str(Path(binary).resolve())
    with TemporaryDirectory(prefix="codeguard-sast-") as directory:
        root = Path(directory)
        mapping = {}
        for index, source in enumerate(sources):
            # GitHub paths and repo-level configuration never reach the scanner.
            basename = f"file_{index}{PurePosixPath(source.path).suffix}"
            mapping[basename] = source
            (root / basename).write_text(source.text, encoding="utf-8")
        try:
            code, output, _ = bounded_process([
                binary, "scan", "--config", str(RULES), "--json",
                "--metrics=off", "--disable-version-check", "--no-git-ignore",
                "--disable-nosem", "--no-rewrite-rule-ids", "--max-memory", "256", "--jobs", "1", "--timeout", "3", "--max-target-bytes", "90000",
                *mapping,
            ], cwd=root, timeout=35, memory=4_000_000_000)
            if code != 0:
                return [], "failed"
            data = json.loads(output)
            if data.get("version") != SEMGREP_VERSION:
                return [], "version_mismatch"
        except ProcessFailure as exc:
            return [], "timed_out" if str(exc) == "Tool timed out" else "unavailable"
        except ValueError:
            return [], "failed"

    results = []
    for item in data["results"]:
        source = mapping.get(Path(item["path"]).name)
        if source is None:
            continue
        first, last = item["start"]["line"], item["end"]["line"]
        line = next((line for line in source.added if first <= line <= last), None)
        if line is None:
            continue
        extra = item["extra"]
        results.append(finding(
            source, line, "semgrep", item["check_id"][-200:],
            SEVERITIES.get(extra["severity"], "low"), extra["message"],
        ))
    return results, "partial" if data.get("errors") else "completed"
