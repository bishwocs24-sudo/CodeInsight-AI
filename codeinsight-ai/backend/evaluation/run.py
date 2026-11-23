"""Evaluate unique finding locations on the bundled labeled fixture set."""

import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter

from app.platform_review.evidence import Source
from app.platform_review.pipeline import run_review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true", help="Require the curated benchmark to remain perfect")
    parser.add_argument("--input-usd-per-million", type=float)
    parser.add_argument("--output-usd-per-million", type=float)
    args = parser.parse_args()
    cases = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    tp = fp = fn = tn = 0
    durations = []
    details = []
    counts = {"input": 0, "output": 0}
    for case in cases:
        lines = case["code"].splitlines()
        source = Source(case["path"], case["code"], {number: lines[number - 1] for number in case["added"]})
        started = perf_counter()
        findings, result = run_review([source], 0)
        durations.append((perf_counter() - started) * 1000)
        expected = set(case["expected"])
        reported = {row["line"] for row in findings}
        tp += len(expected & reported)
        fp += len(reported - expected)
        fn += len(expected - reported)
        tn += len(set(case["added"]) - expected - reported)
        tokens = result["ai_tokens"] or {}
        counts["input"] += tokens.get("promptTokenCount", 0)
        counts["output"] += tokens.get("candidatesTokenCount", 0)
        details.append({
            "case": case["case"], "expected": sorted(expected), "reported": sorted(reported),
            "semgrep": result["semgrep"], "ai": result["ai"],
        })

    summary = {
        "cases": len(cases), "true_positive": tp, "false_positive": fp,
        "false_negative": fn, "true_negative": tn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "median_latency_ms": round(median(durations)), "ai_tokens": counts, "details": details,
    }
    if args.input_usd_per_million is not None and args.output_usd_per_million is not None:
        summary["estimated_provider_cost_usd_per_review"] = (
            counts["input"] * args.input_usd_per_million + counts["output"] * args.output_usd_per_million
        ) / (1_000_000 * len(cases))
    print(json.dumps(summary, indent=2))
    if args.gate and (fp or fn or any(row["semgrep"] not in {"completed", "partial"} for row in details)):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
