import hashlib
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
LANGUAGES = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".c": "c", ".h": "c",
    ".cc": "cpp", ".cpp": "cpp", ".hpp": "cpp",
}
EXTENSIONS = {"python": ".py", "javascript": ".js", "typescript": ".ts", "c": ".c", "cpp": ".cpp"}
Severity = Literal["high", "medium", "low"]


@dataclass
class Source:
    path: str
    text: str
    added: dict[int, str]

    @property
    def language(self):
        return LANGUAGES.get(PurePosixPath(self.path).suffix)


def added_lines(patch: str) -> dict[int, str]:
    result = {}
    line = None
    for part in patch.split("\n"):
        hunk = HUNK.match(part)
        if hunk:
            line = int(hunk[1])
        elif line is not None and part.startswith(("+", " ")):
            if part.startswith("+"):
                result[line] = part[1:].removesuffix("\r")
            line += 1
    return result


def finding(source: Source, line: int, engine: str, rule: str, severity: Severity, message: str):
    evidence = source.added[line]
    fingerprint = hashlib.sha256(f"{engine}\0{rule}\0{source.path}\0{evidence}".encode()).hexdigest()
    return {
        "source": engine, "rule_id": rule, "path": source.path, "line": line,
        "severity": severity, "message": message, "fingerprint": fingerprint,
        "evidence_sha256": hashlib.sha256(evidence.encode()).hexdigest(),
    }


class AIFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    path: str = Field(min_length=1, max_length=500)
    line: int = Field(ge=1)
    quote: str = Field(min_length=1, max_length=500)
    severity: Severity
    message: str = Field(min_length=1, max_length=320)


def validate_ai(raw: object, sources: list[Source]) -> list[dict]:
    by_path = {file.path: file for file in sources}
    accepted = {}
    if not isinstance(raw, dict) or not isinstance(raw.get("findings"), list):
        raise ValueError("Invalid AI response envelope")
    for item in raw["findings"][:20]:
        try:
            candidate = AIFinding.model_validate(item)
        except ValueError:
            continue
        file = by_path.get(candidate.path)
        if file and candidate.quote.strip() and file.added.get(candidate.line) == candidate.quote:
            accepted.setdefault(
                (file.path, candidate.line),
                finding(file, candidate.line, "ai", "AI-REVIEW", candidate.severity, candidate.message),
            )
    return list(accepted.values())
