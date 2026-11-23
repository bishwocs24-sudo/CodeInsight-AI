"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Activity, ArrowDownToLine, Braces, CircleCheck, GitPullRequest, ListFilter, Plus, ScanLine, ShieldCheck, X } from "lucide-react";
import {
  cancelAutomationJob, exportAutomationJob, getAutomationCapabilities, getAutomationJob,
  getAutomationJobs, queueReview, submitFindingFeedback,
  type AutomationFinding, type AutomationJob, type AutomationJobDetail, type FindingVerdict,
} from "@/lib/api";

const statusLabels: Record<string, string> = {
  completed: "Completed", queued: "Queued", running: "Running", publishing: "Publishing",
  cancelled: "Cancelled", failed: "Failed", superseded: "Superseded",
};
const active = (job: AutomationJob) => ["queued", "running", "publishing"].includes(job.status);
const humanize = (value: string) => value.replaceAll("_", " ");
const jobTitle = (job: AutomationJob) => job.repository
  ? `${job.repository} #${job.pull_number}` : "Snippet review";

function Status({ job }: { job: AutomationJob }) {
  return <span className={`queue-status status-${job.status}`}><i />{statusLabels[job.status]}</span>;
}

function FindingCard({ finding, github, onFeedback }: {
  finding: AutomationFinding;
  github: string | null;
  onFeedback: (verdict: FindingVerdict) => void;
}) {
  const location = `${finding.path}:${finding.line}`;
  const fileUrl = github && `${github}/${finding.path.split("/").map(encodeURIComponent).join("/")}#L${finding.line}`;
  return (
    <article className="queue-finding">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`queue-severity severity-${finding.severity}`}>{finding.severity}</span>
        <span className="queue-source">{finding.source === "ai" ? "AI suggestion" : finding.source === "static" ? "Static analysis" : "Semgrep"}</span>
        {finding.suppressed && <span className="text-xs text-slate-400">Suppressed</span>}
      </div>
      <p className="mt-3 break-words text-sm leading-6">{finding.message}</p>
      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-400">
        {fileUrl ? <a className="queue-link break-all" href={fileUrl} target="_blank" rel="noreferrer">{location}</a>
          : <code className="break-all text-teal-200">{location}</code>}
        <code className="break-all">{finding.rule_id}</code>
        <code title={finding.evidence_sha256}>SHA-256 {finding.evidence_sha256.slice(0, 12)}</code>
      </div>
      <label className="mt-4 flex w-fit items-center gap-2 text-xs text-slate-400">
        Feedback
        <select className="queue-input py-1" value={finding.verdict ?? "clear"}
          onChange={(event) => onFeedback(event.target.value as FindingVerdict)}>
          <option value="clear">Unreviewed</option>
          <option value="confirmed">Confirmed</option>
          <option value="false_positive">False positive</option>
        </select>
      </label>
    </article>
  );
}

export default function ReviewQueuePage() {
  const [jobs, setJobs] = useState<AutomationJob[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<AutomationJobDetail | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [filter, setFilter] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [composer, setComposer] = useState(false);
  const [language, setLanguage] = useState("python");
  const [source, setSource] = useState("");
  const [tests, setTests] = useState("");
  const [sandbox, setSandbox] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getAutomationCapabilities().then((data) => setSandbox(data.sandbox)).catch(() => {});
  }, []);

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const rows = await getAutomationJobs();
        if (!stopped) {
          setJobs(rows);
          setLoaded(true);
          setLoadError("");
          setSelected((id) => id && rows.some((job) => job.id === id) ? id : rows[0]?.id ?? null);
        }
      } catch {
        if (!stopped) setLoadError("Couldn’t load review jobs. Retrying…");
      } finally {
        if (!stopped) timer = setTimeout(refresh, 3000);
      }
    }
    void refresh();
    return () => { stopped = true; clearTimeout(timer); };
  }, []);

  useEffect(() => {
    if (!selected) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const data = await getAutomationJob(selected!);
        if (!stopped) setDetail(data);
      } catch {
        if (!stopped) setError("Couldn’t load this review. Retrying…");
      } finally {
        if (!stopped) timer = setTimeout(refresh, 3500);
      }
    }
    void refresh();
    return () => { stopped = true; clearTimeout(timer); };
  }, [selected]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const job = await queueReview(language, source, sandbox && language === "python" ? tests || undefined : undefined);
      setJobs(await getAutomationJobs());
      setSelected(job.id);
      setSource("");
      setTests("");
      setComposer(false);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Couldn’t queue the review.");
    } finally {
      setBusy(false);
    }
  }

  async function action(work: () => Promise<unknown>) {
    setError("");
    try {
      await work();
      if (selected) {
        const fresh = await getAutomationJob(selected);
        setDetail(fresh);
        setJobs((rows) => rows.map((row) => row.id === fresh.id ? fresh : row));
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "The request failed.");
    }
  }

  const current = detail?.id === selected ? detail : null;
  const visible = jobs.filter((job) => filter === "all" || (filter === "active" ? active(job) : job.status === filter));
  const cards = [
    { name: "Recent reviews", total: jobs.length, icon: ScanLine },
    { name: "In progress", total: jobs.filter(active).length, icon: Activity },
    { name: "Completed", total: jobs.filter((job) => job.status === "completed").length, icon: CircleCheck },
    { name: "GitHub pull requests", total: jobs.filter((job) => job.repository).length, icon: GitPullRequest },
  ];
  const githubUrl = current?.repository && current.head_sha
    ? `https://github.com/${current.repository}/blob/${current.head_sha}` : null;

  return (
    <div className="queue-workspace">
      <header className="queue-hero">
        <div>
          <div className="queue-heading-icon"><ShieldCheck size={22} /></div>
          <h1>Review queue</h1>
          <p>Track pull request and snippet reviews, inspect line evidence, and triage findings.</p>
        </div>
        <button className="queue-primary" onClick={() => { setComposer(!composer); setError(""); }}
          aria-expanded={composer} aria-controls="queue-composer">
          {composer ? <X size={17} /> : <Plus size={17} />}{composer ? "Close" : "New scan"}
        </button>
      </header>

      {(error || loadError) && <p role="alert" className="queue-alert">{error || loadError}</p>}
      {composer && (
        <form id="queue-composer" onSubmit={submit} className="queue-panel mb-6 p-5">
          <h2 className="text-lg font-semibold">Scan a code snippet</h2>
          <label className="mt-4 grid max-w-xs gap-1.5 text-sm">Language
            <select className="queue-input" value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option value="python">Python</option><option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option><option value="c">C</option><option value="cpp">C++</option>
            </select>
          </label>
          <label className="mt-4 grid gap-1.5 text-sm">Source code
            <textarea className="queue-input min-h-36 font-mono" value={source} onChange={(event) => setSource(event.target.value)}
              required maxLength={40_000} spellCheck={false} placeholder="Paste source code" />
          </label>
          {sandbox && language === "python" && (
            <label className="mt-4 grid gap-1.5 text-sm">Python unittest code (optional)
              <span className="text-xs text-slate-400">Import your code from <code>submission</code>. Tests run in an offline container.</span>
              <textarea className="queue-input min-h-28 font-mono" value={tests} onChange={(event) => setTests(event.target.value)}
                maxLength={20_000} spellCheck={false} />
            </label>
          )}
          <button type="submit" className="queue-primary mt-4" disabled={busy || !source.trim()}>
            <ScanLine size={17} /> {busy ? "Queueing…" : "Queue review"}
          </button>
        </form>
      )}

      <div className="queue-metrics">
        {cards.map(({ name, total, icon: Icon }) => (
          <div className="queue-panel queue-metric" key={name}>
            <Icon size={17} aria-hidden />
            <span>{name}</span>
            <strong>{loaded ? total : "–"}</strong>
          </div>
        ))}
      </div>

      <div className="queue-split">
        <section className="queue-panel min-w-0">
          <div className="queue-toolbar">
            <h2>Activity</h2>
            <label className="flex items-center gap-2 text-slate-400">
              <ListFilter size={15} /><span className="sr-only">Filter reviews by status</span>
              <select className="queue-input py-1 text-xs" value={filter} onChange={(event) => setFilter(event.target.value)}>
                <option value="all">All statuses</option><option value="active">In progress</option>
                {["completed", "failed", "cancelled", "superseded"].map((value) =>
                  <option key={value} value={value}>{statusLabels[value]}</option>)}
              </select>
            </label>
          </div>
          {visible.length === 0 && <p className="queue-empty">{!loaded ? "Loading activity…" :
            jobs.length ? "No matching reviews." : "No reviews yet. Queue a snippet scan to get started."}</p>}
          <ul aria-label="Recent jobs">
            {visible.map((job) => (
              <li key={job.id}>
                <button className="queue-job" aria-current={selected === job.id}
                  onClick={() => { setSelected(job.id); setSeverity("all"); setError(""); }}>
                  {job.repository ? <GitPullRequest size={18} /> : <Braces size={18} />}
                  <span className="min-w-0 flex-1"><strong>{jobTitle(job)}</strong>
                    <small><time dateTime={job.created_at}>{new Date(job.created_at).toLocaleString(undefined, {
                      dateStyle: "medium", timeStyle: "short",
                    })}</time></small></span>
                  <Status job={job} />
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="queue-panel min-w-0" aria-label="Review detail">
          {!current ? (
            <div className="queue-detail-empty">
              <ScanLine size={27} /><h2>{selected ? "Loading review…" : "Review details"}</h2>
              {!selected && <p>Select a review to inspect findings and scan coverage.</p>}
            </div>
          ) : (
            <>
              <div className="queue-toolbar flex-wrap">
                <div className="min-w-0"><h2 className="break-words">{jobTitle(current)}</h2>
                  <div className="mt-2 flex items-center gap-2"><Status job={current} />
                    {current.head_sha && <code className="text-xs text-slate-400">{current.head_sha.slice(0, 8)}</code>}</div>
                </div>
                {["queued", "running"].includes(current.status) && (
                  <button className="queue-secondary" onClick={() => action(() => cancelAutomationJob(current.id))}>Cancel</button>
                )}
                {current.result && <button className="queue-secondary" onClick={() => action(() => exportAutomationJob(current.id))}>
                  <ArrowDownToLine size={15} /> SARIF
                </button>}
              </div>
              <div className="p-4 sm:p-5">
                {current.error && <p className="mb-4 text-sm text-rose-300">{current.error}</p>}
                {current.result && (
                  <dl className="queue-coverage">
                    <div><dt>Files</dt><dd>{current.result.files_reviewed} reviewed · {current.result.files_skipped} skipped</dd></div>
                    <div><dt>Semgrep</dt><dd>{humanize(current.result.semgrep)}</dd></div>
                    <div><dt>AI</dt><dd>{humanize(current.result.ai)}</dd></div>
                    {current.result.verification && <div><dt>Tests</dt><dd>{humanize(current.result.verification.status)}</dd></div>}
                    {current.result.publication && <div><dt>GitHub</dt><dd>{humanize(current.result.publication)}</dd></div>}
                    <div><dt>Duration</dt><dd>{(current.result.duration_ms / 1000).toFixed(1)} s</dd></div>
                  </dl>
                )}
                {current.result && (
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h3 className="font-medium">Findings <span className="text-slate-400">({current.findings.length})</span></h3>
                    <label><span className="sr-only">Filter findings by severity</span>
                      <select value={severity} onChange={(event) => setSeverity(event.target.value)} className="queue-input py-1 text-xs">
                        <option value="all">All severities</option><option value="high">High</option>
                        <option value="medium">Medium</option><option value="low">Low</option>
                      </select>
                    </label>
                  </div>
                )}
                <div className="space-y-3">
                  {current.findings.filter((finding) => severity === "all" || finding.severity === severity).map((finding) =>
                    <FindingCard key={finding.id} finding={finding} github={githubUrl}
                      onFeedback={(verdict) => action(() => submitFindingFeedback(current.id, finding.id, verdict))} />
                  )}
                  {current.result && current.findings.filter((item) => severity === "all" || item.severity === severity).length === 0 &&
                    <p className="text-sm text-slate-400">{severity === "all" ? "This review recorded no findings." : "No findings at this severity."}</p>}
                  {!current.result && active(current) && <p className="text-sm text-slate-400" role="status">The review will update as the worker progresses.</p>}
                  {current.result?.findings_truncated && <p className="text-xs text-slate-400">Showing the first 150 findings by severity.</p>}
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
