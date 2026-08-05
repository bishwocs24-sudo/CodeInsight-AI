"use client";

import { useEffect, useRef, useState } from "react";
import {
  ScanSearch,
  BookOpen,
  Wand2,
  FlaskConical,
  ShieldCheck,
  Gauge,
  Download,
  FileUp,
  FileText,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { CodeEditor } from "@/components/code-editor";
import { ScoreCard } from "@/components/score-card";
import { CopyButton } from "@/components/copy-button";
import { DiffViewer } from "@/components/diff-viewer";
import { runAnalysis, uploadCodeFile, downloadReviewPdf, ApiError } from "@/lib/api";
import { LANGUAGES } from "@/lib/types";
import type { Language, ReviewResponse, ReviewType } from "@/lib/types";

const ACTIONS: { type: ReviewType; label: string; icon: typeof ScanSearch }[] = [
  { type: "review", label: "Review Code", icon: ScanSearch },
  { type: "explain", label: "Explain Code", icon: BookOpen },
  { type: "refactor", label: "Refactor", icon: Wand2 },
  { type: "tests", label: "Generate Tests", icon: FlaskConical },
  { type: "security", label: "Security Scan", icon: ShieldCheck },
  { type: "complexity", label: "Complexity Analysis", icon: Gauge },
];

const DEFAULT_CODE = `def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
`;

const AUTOSAVE_KEY = "codeinsight:draft";

export default function NewReviewPage() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [language, setLanguage] = useState<Language>("python");
  const [activeAction, setActiveAction] = useState<ReviewType | null>(null);
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(AUTOSAVE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as { code: string; language: Language };
        if (parsed.code) setCode(parsed.code);
        if (parsed.language) setLanguage(parsed.language);
      }
    } catch {
      // ignore corrupt/missing draft
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(AUTOSAVE_KEY, JSON.stringify({ code, language }));
  }, [code, language]);

  async function handleAction(type: ReviewType) {
    if (!code.trim()) {
      setError("Paste some code first.");
      return;
    }
    setLoading(true);
    setActiveAction(type);
    setError(null);
    try {
      const res = await runAnalysis(type, code, language);
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        if (!loading) handleAction("review");
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, language, loading]);

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const uploaded = await uploadCodeFile(file);
      setCode(uploaded.code);
      setLanguage(uploaded.language);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't read that file.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  function downloadJson() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `codeinsight-review-${result.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight">New Review</h1>
          <p className="text-sm text-muted-foreground">
            Paste code, pick an action, get results. <kbd className="rounded bg-muted px-1.5 py-0.5 text-xs">Ctrl+Enter</kbd> to review.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".py,.js,.jsx,.ts,.tsx,.go,.rs,.c,.h,.cpp,.hpp,.cs,.kt,.swift,.rb,.php,.java"
            className="hidden"
            onChange={handleFileSelect}
          />
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
            Upload File
          </Button>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            className="rounded-xl border border-border bg-muted px-3 py-2 text-sm outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary/40"
          >
            {LANGUAGES.map((l) => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        {ACTIONS.map((a) => (
          <Button
            key={a.type}
            variant={activeAction === a.type ? "default" : "outline"}
            size="sm"
            disabled={loading}
            onClick={() => handleAction(a.type)}
          >
            {loading && activeAction === a.type ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <a.icon className="h-4 w-4" />
            )}
            {a.label}
          </Button>
        ))}
        {result && (
          <>
            <Button variant="ghost" size="sm" onClick={downloadJson}>
              <Download className="h-4 w-4" /> Export JSON
            </Button>
            <Button variant="ghost" size="sm" onClick={() => downloadReviewPdf(result.id)}>
              <FileText className="h-4 w-4" /> Export PDF
            </Button>
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <CodeEditor value={code} language={language} onChange={setCode} />

        <div className="space-y-4">
          {error && (
            <Card className="border-red-500/30">
              <CardContent className="p-4 text-sm text-red-400">{error}</CardContent>
            </Card>
          )}

          {!result && !error && (
            <Card>
              <CardContent className="flex h-[480px] items-center justify-center p-4 text-center text-sm text-muted-foreground">
                Run an action to see results here.
              </CardContent>
            </Card>
          )}

          {result && (
            <div className="max-h-[480px] space-y-4 overflow-y-auto scrollbar-thin pr-1">
              {result.scores && (
                <div className="grid grid-cols-2 gap-3">
                  <ScoreCard label="Overall" score={result.scores.overall} />
                  <ScoreCard label="Security" score={result.scores.security} />
                  <ScoreCard label="Performance" score={result.scores.performance} />
                  <ScoreCard label="Maintainability" score={result.scores.maintainability} />
                </div>
              )}

              {result.summary && (
                <Card>
                  <CardContent className="p-5 text-sm">{result.summary}</CardContent>
                </Card>
              )}

              {result.security_issues.length > 0 && (
                <Card>
                  <CardContent className="space-y-3 p-5">
                    <h3 className="text-sm font-medium">Security issues</h3>
                    {result.security_issues.map((issue, i) => (
                      <div key={i} className="rounded-xl bg-muted p-3">
                        <div className="mb-1 flex items-center justify-between">
                          <span className="text-sm font-medium">{issue.title}</span>
                          <Badge tone={issue.severity}>{issue.severity}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{issue.description}</p>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {result.bugs.length > 0 && (
                <Card>
                  <CardContent className="space-y-3 p-5">
                    <h3 className="text-sm font-medium">Bugs found</h3>
                    {result.bugs.map((bug, i) => (
                      <div key={i} className="rounded-xl bg-muted p-3">
                        <div className="mb-1 flex items-center justify-between">
                          <span className="text-sm">{bug.description}</span>
                          <Badge tone={bug.severity}>{bug.severity}</Badge>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {result.explanation && (
                <Card>
                  <CardContent className="p-5 text-sm whitespace-pre-wrap">{result.explanation}</CardContent>
                </Card>
              )}

              {result.refactored_code && (
                <Card>
                  <CardContent className="p-5">
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="text-sm font-medium">Refactored code (diff)</h3>
                      <CopyButton text={result.refactored_code} />
                    </div>
                    <DiffViewer original={code} refactored={result.refactored_code} />
                  </CardContent>
                </Card>
              )}

              {result.unit_tests && (
                <Card>
                  <CardContent className="p-5">
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="text-sm font-medium">Generated tests</h3>
                      <CopyButton text={result.unit_tests} />
                    </div>
                    <pre className="overflow-x-auto rounded-xl bg-muted p-3 text-xs">
                      <code>{result.unit_tests}</code>
                    </pre>
                  </CardContent>
                </Card>
              )}

              {result.complexity && (
                <Card>
                  <CardContent className="space-y-2 p-5 text-sm">
                    <p><span className="text-muted-foreground">Time:</span> {String(result.complexity.time_complexity)}</p>
                    <p><span className="text-muted-foreground">Space:</span> {String(result.complexity.space_complexity)}</p>
                    <p className="text-muted-foreground">{String(result.complexity.explanation)}</p>
                  </CardContent>
                </Card>
              )}

              {(result.strengths.length > 0 || result.weaknesses.length > 0) && (
                <div className="grid grid-cols-2 gap-3">
                  {result.strengths.length > 0 && (
                    <Card>
                      <CardContent className="p-4">
                        <h3 className="mb-2 text-xs font-medium text-emerald-400">Strengths</h3>
                        <ul className="space-y-1 text-xs text-muted-foreground">
                          {result.strengths.map((s, i) => <li key={i}>• {s}</li>)}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                  {result.weaknesses.length > 0 && (
                    <Card>
                      <CardContent className="p-4">
                        <h3 className="mb-2 text-xs font-medium text-orange-400">Weaknesses</h3>
                        <ul className="space-y-1 text-xs text-muted-foreground">
                          {result.weaknesses.map((s, i) => <li key={i}>• {s}</li>)}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
