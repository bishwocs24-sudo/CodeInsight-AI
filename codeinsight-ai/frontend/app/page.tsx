import Link from "next/link";
import { Braces, GitPullRequest, ScanLine, ShieldCheck } from "lucide-react";

const workflow = [
  {
    icon: GitPullRequest,
    title: "Review changes",
    body: "Queue a snippet scan or configure a GitHub App to review added lines at a specific commit.",
  },
  {
    icon: ScanLine,
    title: "Inspect the evidence",
    body: "See which lines Semgrep and the built-in analyzer flagged. If Gemini is enabled, AI suggestions must cite an exact changed line.",
  },
  {
    icon: Braces,
    title: "Triage and export",
    body: "Mark findings as confirmed or false positives, then export the review as SARIF.",
  },
];

export default function LandingPage() {
  return (
    <main className="queue-workspace max-w-6xl px-5 py-6 sm:px-8">
      <nav className="flex items-center justify-between gap-4 py-2" aria-label="Main">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <ShieldCheck className="text-teal-300" size={21} aria-hidden /> CodeGuard AI
        </Link>
        <Link href="/login" className="queue-secondary">Sign in</Link>
      </nav>

      <section className="release-hero mt-8 rounded-2xl border">
        <div>
          <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">
            Code reviews with line-level evidence
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-300">
            Scan source code for security and reliability issues, inspect the affected lines, and export the results.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link href={process.env.NEXT_PUBLIC_DEMO_ONLY === "1" ? "/scan" : "/dashboard/review-queue"} className="queue-primary">Start a code scan</Link>
            <Link href="/demo" className="queue-secondary">Explore a sample review</Link>
          </div>
        </div>
        <aside className="queue-panel min-w-0 p-5" aria-label="Example of a review finding">
          <div className="flex flex-wrap items-center gap-2">
            <span className="queue-severity severity-medium">Medium</span>
            <span className="queue-source">Semgrep</span>
          </div>
          <p className="mt-4 text-lg font-medium">Mutable default argument</p>
          <pre className="mt-3 overflow-x-auto rounded-md bg-slate-950 p-3 text-xs text-teal-200"><code>def add_label(label, labels=[]):</code></pre>
          <p className="mt-4 text-sm leading-6 text-slate-300">Initialize mutable defaults inside the function to avoid sharing state.</p>
        </aside>
      </section>

      <section className="mt-10" aria-labelledby="workflow-heading">
        <h2 id="workflow-heading" className="text-xl font-semibold">Review workflow</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {workflow.map(({ icon: Icon, title, body }) => (
            <article className="queue-panel p-5" key={title}>
              <Icon size={20} className="text-teal-300" aria-hidden />
              <h3 className="mt-4 font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300">{body}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
