"""Verify a deployed CodeGuard instance with one fixed, harmless snippet."""

import argparse
import time
from getpass import getpass
from urllib.parse import urlsplit

import httpx

SAMPLE = "def add_label(label, labels=[]):\n    labels.append(label)\n    return labels\n"


def check(origin, email, password, wait_seconds):
    with httpx.Client(base_url=origin, timeout=10, trust_env=False) as client:
        assert_response(client.get("/ready").json().get("status") == "ready", "API readiness failed")
        page = client.get("/demo/")
        assert_response(page.status_code == 200 and "Sample review" in page.text, "Demo page unavailable")
        auth = client.post("/auth/login", json={"email": email, "password": password})
        auth.raise_for_status()
        client.headers["Authorization"] = f"Bearer {auth.json()['access_token']}"

        reply = client.post("/automation/jobs", json={"language": "python", "code": SAMPLE})
        reply.raise_for_status()
        path = f"/automation/jobs/{reply.json()['id']}"
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            reply = client.get(path)
            reply.raise_for_status()
            job = reply.json()
            if job["status"] == "completed":
                break
            if job["status"] in {"cancelled", "failed", "superseded"}:
                raise RuntimeError(f"Review ended with status {job['status']}")
            time.sleep(2)
        else:
            raise RuntimeError("Review exceeded the wait limit")
        assert_response(job["result"]["semgrep"] == "completed", "Semgrep did not complete")
        required = {"python-mutable-default", "PY005"}
        assert_response(required <= {item["rule_id"] for item in job["findings"]}, "Expected findings are missing")
        export = client.get(path + "/sarif")
        export.raise_for_status()
        rule_ids = {item["ruleId"] for run in export.json()["runs"] for item in run["results"]}
        assert_response(required <= rule_ids, "Expected SARIF results are missing")
        return job["id"]


def assert_response(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin", help="HTTPS deployment origin or an HTTP loopback origin")
    parser.add_argument("email", help="Email of a provisioned test operator")
    parser.add_argument("--wait-seconds", type=int, default=90)
    args = parser.parse_args()
    parsed = urlsplit(args.origin)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not parsed.hostname or parsed.username or parsed.password or parsed.path.rstrip("/")
        or parsed.query or parsed.fragment
        or (parsed.scheme != "https" and not (local and parsed.scheme == "http"))
    ):
        parser.error("Enter an HTTPS origin with no credentials, path, query or fragment")
    try:
        job_id = check(args.origin, args.email, getpass("Operator password: "), args.wait_seconds)
    except (httpx.HTTPError, RuntimeError, KeyError, ValueError) as exc:
        parser.exit(1, f"Deployment check failed: {exc}\n")
    print(f"Deployment check passed. Review job {job_id}")


if __name__ == "__main__":
    main()
