"""Regenerate the public demo from the real, deterministic review pipeline."""

import json
import os
import sys

from app.platform_review.evidence import Source
from app.platform_review.pipeline import run_review
from app.platform_review.sarif import build_sarif

CODE = """def add_label(label, labels=[]):
    labels.append(label)
    return labels


first = add_label("review")
second = add_label("ready")
"""


def main():
    os.environ["PR_AI_ENABLED"] = "false"
    file = Source("labels.py", CODE, dict(enumerate(CODE.splitlines(), start=1)))
    findings, result = run_review([file], 0)
    if result["semgrep"] != "completed":
        sys.exit(f"Semgrep must complete to generate the demo ({result['semgrep']}).")
    for item in findings:
        item["suppressed"] = False
    demo = {"source": CODE, "path": file.path, "scan": result, "findings": findings,
            "sarif": build_sarif(findings, result["ruleset"])}
    print(json.dumps(demo, indent=2))


if __name__ == "__main__":
    main()
