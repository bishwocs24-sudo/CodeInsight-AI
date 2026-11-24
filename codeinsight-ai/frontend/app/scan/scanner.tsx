"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { Code2, Download, FileUp, ScanLine, ShieldCheck } from "lucide-react";

const languages = [
  { id: "python", label: "Python", extensions: ["py"] },
  { id: "javascript", label: "JavaScript", extensions: ["js", "mjs", "jsx"] },
  { id: "typescript", label: "TypeScript", extensions: ["ts", "tsx"] },
  { id: "c", label: "C", extensions: ["c", "h"] },
  { id: "cpp", label: "C++", extensions: ["cpp", "hpp", "cc", "cxx"] },
] as const;
const limit = 24_000;
const example = "def add_label(label, labels=[]):\n    labels.append(label)\n    return labels\n";

type Finding = { rule_id: string; severity: string; message: string; line: number; evidence: string };
type ScanResult = { findings: Finding[]; finding_count: number; errors: string[]; lines_of_code: number; engine: string };
type Review = { data: ScanResult; filename: string };

export function Scanner() {
  const [language, setLanguage] = useState<string>("python");
  const [code, setCode] = useState("");
  const [filename, setFilename] = useState("");
  const [review, setReview] = useState<Review | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const bytes = new TextEncoder().encode(code).length;

  async function loadFile(file: File) {
    const extension = file.name.split(".").pop()?.toLowerCase();
    const detected = languages.find((item) => item.extensions.some((ext) => ext === extension));
    if (!detected || file.size > limit) {
      setError("Choose a supported source file of 24 KB or less.");
      return;
    }
    try {
      const source = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      setCode(source);
      setLanguage(detected.id);
      setFilename(file.name);
      setReview(null);
      setError("");
    } catch {
      setError("Choose a source file encoded as UTF-8.");
    }
  }

  async function scan() {
    setError("");
    setReview(null);
    setPending(true);
    try {
      const response = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language }),
        signal: AbortSignal.timeout(20_000),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "The scan failed. Try again.");
      const defaultName = `snippet.${languages.find((item) => item.id === language)?.extensions[0] ?? "txt"}`;
      setReview({ data, filename: filename || defaultName });
    } catch (cause) {
      const message = cause instanceof Error && cause.constructor === Error
        ? cause.message
        : "The scanner could not be reached. Try again.";
      setError(message);
    } finally {
      setPending(false);
    }
  }

  function exportReport({ data, filename }: Review) {
    const sarif = {
      $schema: "https://json.schemastore.org/sarif-2.1.0.json",
      version: "2.1.0",
      runs: [{
        tool: { driver: { name: "CodeGuard AI", version: data.engine } },
        invocations: [{ executionSuccessful: data.errors.length === 0 && data.finding_count <= data.findings.length }],
        results: data.findings.map((finding) => ({
          ruleId: finding.rule_id,
          level: finding.severity === "high" ? "error" : "warning",
          message: { text: finding.message },
          locations: [{ physicalLocation: {
            artifactLocation: { uri: encodeURIComponent(filename) },
            region: { startLine: finding.line, snippet: { text: finding.evidence } },
          } }],
        })),
      }],
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(sarif, null, 2)], { type: "application/sarif+json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "codeguard-review.sarif";
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1_000);
  }

  return (
    <main className="queue-workspace scanner-shell px-5 py-6 sm:px-8">
      <nav aria-label="Main" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <Link href="/" className="flex items-center gap-2 font-semibold"><ShieldCheck className="text-teal-300" size={21} aria-hidden /> CodeGuard AI</Link>
        <div className="flex flex-wrap items-center gap-4">
          <Link href="/demo" className="text-sm text-slate-300 hover:text-white">Sample review</Link>
          <Link href="/login" className="queue-secondary">Sign in</Link>
        </div>
      </nav>
      <header className="my-8 sm:my-11">
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Live code scanner</h1>
        <p className="mt-3 max-w-2xl text-slate-300">Paste a snippet or upload a source file to find issues and inspect the lines behind each finding.</p>
      </header>
      <div className="scanner-grid">
        <form className="queue-panel min-w-0 overflow-hidden" onSubmit={(event) => { event.preventDefault(); void scan(); }}>
          <fieldset disabled={pending} className="min-w-0">
            <div className="scanner-panel-header">
              <h2 className="flex items-center gap-2 font-semibold"><Code2 size={18} aria-hidden className="text-teal-300" /> Source code</h2>
              <div className="flex flex-wrap gap-2">
                <button type="button" className="queue-secondary" onClick={() => {
                  setLanguage("python"); setCode(example); setFilename(""); setReview(null); setError("");
                }}>Load example</button>
                <button type="button" className="queue-secondary" onClick={() => input.current?.click()}><FileUp size={16} aria-hidden /> Upload file</button>
                <input ref={input} type="file" hidden accept={languages.flatMap((item) => item.extensions.map((ext) => `.${ext}`)).join(",")}
                  onChange={(event) => {
                    const file = event.currentTarget.files?.[0];
                    if (file) void loadFile(file);
                    event.currentTarget.value = "";
                  }} />
              </div>
            </div>
            <div className="p-4 sm:p-5">
              <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-2">
                <label htmlFor="scanner-language" className="text-sm font-medium">Language</label>
                <select id="scanner-language" value={language} className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                  onChange={(event) => { setLanguage(event.target.value); setReview(null); }}>
                  {languages.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
                </select>
                {filename && <span className="break-all text-sm text-slate-400">{filename}</span>}
              </div>
              <label htmlFor="scanner-code" className="sr-only">Source code to scan</label>
              <textarea id="scanner-code" className="scanner-editor" value={code}
                onChange={(event) => { setCode(event.target.value); setReview(null); setError(""); }}
                spellCheck={false} placeholder="Paste your source code here" />
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                <span className={bytes > limit ? "text-sm text-rose-300" : "text-sm text-slate-400"}>{bytes.toLocaleString()} / 24,000 bytes</span>
                <button type="submit" className="queue-primary" disabled={!code.trim() || bytes > limit || pending}>
                  <ScanLine size={17} aria-hidden /> {pending ? "Scanning…" : "Run scan"}
                </button>
              </div>
              {error && <p role="alert" className="mt-3 text-sm text-rose-300">{error}</p>}
            </div>
          </fieldset>
        </form>
        <section aria-labelledby="scanner-results" className="queue-panel min-w-0 overflow-hidden">
          <div className="scanner-panel-header">
            <h2 id="scanner-results" className="font-semibold">Findings</h2>
            {review && <button type="button" className="queue-secondary" onClick={() => exportReport(review)}><Download size={16} aria-hidden /> SARIF</button>}
          </div>
          <div className="p-4 sm:p-5" aria-live="polite" aria-busy={pending}>
            {!review && <p className="text-slate-400">{pending ? "Analyzing source…" : "Run a scan to see severity, rule IDs, and source lines."}</p>}
            {review && <>
              <p className="mb-4 text-sm text-slate-300">{review.data.finding_count} findings across {review.data.lines_of_code} lines</p>
              {review.data.errors.map((diagnostic) => <p key={diagnostic} className="mb-3 text-sm text-amber-300">{diagnostic}</p>)}
              {review.data.finding_count > review.data.findings.length && <p className="mb-3 text-sm text-amber-300">Showing the first {review.data.findings.length} findings.</p>}
              {review.data.finding_count === 0 && review.data.errors.length === 0 && <p className="text-teal-200">No issues matched the available rules.</p>}
              <ul className="grid gap-3">
                {review.data.findings.map((finding, index) => (
                  <li key={`${finding.rule_id}-${finding.line}-${index}`} className="rounded-lg border border-slate-700 bg-slate-950/60 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`queue-severity severity-${finding.severity}`}>{finding.severity}</span>
                      <span className="text-xs text-slate-400">{finding.rule_id} · line {finding.line}</span>
                    </div>
                    <p className="mt-2 text-sm font-medium">{finding.message}</p>
                    <pre className="mt-2 overflow-x-auto rounded bg-slate-950 p-2 text-xs text-teal-200"><code>{finding.evidence}</code></pre>
                  </li>
                ))}
              </ul>
            </>}
          </div>
        </section>
      </div>
      <p className="mt-5 text-sm text-slate-400">The scanner uses built-in static rules and analyzes source without executing it. Review findings before applying changes.</p>
    </main>
  );
}
