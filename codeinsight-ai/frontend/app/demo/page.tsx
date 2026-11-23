"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowDownToLine, ArrowLeft, ScanLine } from "lucide-react";
import sample from "./sample-review.json";

type Verdict = "unreviewed" | "confirmed" | "false_positive";

export default function DemoPage() {
  const [activeLine, setActiveLine] = useState(sample.findings[0]?.line ?? 1);
  const [verdicts, setVerdicts] = useState<Record<string, Verdict>>({});
  const lines = sample.source.trimEnd().split("\n");

  function download() {
    const report = {
      ...sample.sarif,
      runs: sample.sarif.runs.map((run) => ({
        ...run,
        results: run.results.map((result) => verdicts[result.ruleId] === "false_positive"
          ? { ...result, suppressions: [{ kind: "external", status: "accepted" }] }
          : result),
      })),
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: "application/sarif+json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "codeguard-sample.sarif";
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <main className="queue-workspace max-w-6xl px-5 py-6 sm:px-8">
      <nav className="mb-6 flex flex-wrap items-center justify-between gap-3" aria-label="Sample review">
        <Link className="queue-secondary" href="/"><ArrowLeft size={15} aria-hidden /> Home</Link>
        <Link className="queue-secondary" href="/login">Sign in</Link>
      </nav>
      <header className="queue-hero">
        <div>
          <div className="queue-heading-icon"><ScanLine size={22} aria-hidden /></div>
          <h1>Sample review</h1>
          <p>Explore a recorded Semgrep and static analysis scan. Feedback stays on this page.</p>
        </div>
        <button className="queue-primary" type="button" onClick={download}>
          <ArrowDownToLine size={17} aria-hidden /> Download SARIF
        </button>
      </header>

      <div className="queue-split">
        <section className="queue-panel min-w-0 overflow-hidden" aria-labelledby="sample-source-heading">
          <div className="queue-toolbar">
            <h2 id="sample-source-heading">{sample.path}</h2>
            <span className="text-xs text-slate-400">Python</span>
          </div>
          <ol className="demo-source font-mono text-xs leading-7" aria-label="Sample source lines">
            {lines.map((line, index) => (
              <li key={index} className="flex pr-3" data-selected={activeLine === index + 1}>
                <span className="w-10 shrink-0 pl-3 text-slate-400">{index + 1}</span>
                <code className="whitespace-pre text-teal-100">{line || " "}</code>
              </li>
            ))}
          </ol>
          <p className="px-4 py-4 text-sm leading-6 text-slate-300">
            Both calls share the same default list. The second call changes the list returned by the first.
          </p>
        </section>

        <section className="queue-panel min-w-0" aria-labelledby="sample-findings-heading">
          <div className="queue-toolbar">
            <h2 id="sample-findings-heading">Findings ({sample.findings.length})</h2>
            <span className="queue-status status-completed"><i />Recorded scan</span>
          </div>
          <div className="grid gap-3 p-4">
            {sample.findings.map((finding) => (
              <article className="queue-finding" key={finding.rule_id}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`queue-severity severity-${finding.severity}`}>{finding.severity}</span>
                  <span className="queue-source">{finding.source === "semgrep" ? "Semgrep" : "Static analysis"}</span>
                  {verdicts[finding.rule_id] === "false_positive" && <span className="queue-source">Suppressed</span>}
                </div>
                <p className="mt-3 text-sm leading-6">{finding.message}</p>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-400">
                  <button type="button" className="queue-link font-mono" onClick={() => setActiveLine(finding.line)}
                    aria-pressed={activeLine === finding.line}>{finding.path}:{finding.line}</button>
                  <code className="break-all">{finding.rule_id}</code>
                </div>
                <label className="mt-4 flex w-fit items-center gap-2 text-xs text-slate-400">
                  Feedback
                  <select className="queue-input" aria-label={`Feedback for ${finding.rule_id}`}
                    value={verdicts[finding.rule_id] ?? "unreviewed"}
                    onChange={(event) => {
                      const verdict = event.target.value as Verdict;
                      setVerdicts((current) => ({ ...current, [finding.rule_id]: verdict }));
                    }}>
                    <option value="unreviewed">Unreviewed</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="false_positive">False positive</option>
                  </select>
                </label>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
