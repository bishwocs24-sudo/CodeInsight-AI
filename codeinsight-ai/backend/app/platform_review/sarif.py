from urllib.parse import quote


def build_sarif(findings: list[dict], ruleset: str) -> dict:
    levels = {"high": "error", "medium": "warning", "low": "note"}
    results = []
    for item in findings:
        result = {
            "ruleId": item["rule_id"], "level": levels[item["severity"]],
            "message": {"text": item["message"]},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": quote(item["path"])},
                "region": {"startLine": item["line"]},
            }}],
            "partialFingerprints": {"primaryLocationLineHash": item["evidence_sha256"]},
            "properties": {"source": item["source"]},
        }
        if item["suppressed"]:
            result["suppressions"] = [{"kind": "external", "status": "accepted"}]
        results.append(result)
    return {"version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "CodeGuard AI",
                            "version": ruleset}},
        "results": results,
    }]}
