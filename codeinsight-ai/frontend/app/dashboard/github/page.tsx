"use client";

import { useState } from "react";
import { Github, Loader2, Star, FileCode, Gauge, ScanSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { getRepoHealthScore, importGitHubRepo, reviewGitHubFile, ApiError } from "@/lib/api";
import type { GitHubImportResponse, RepoHealthResponse, ReviewResponse } from "@/lib/types";

function severityTone(score: number): "success" | "medium" | "high" | "critical" {
  if (score >= 80) return "success";
  if (score >= 60) return "medium";
  if (score >= 40) return "high";
  return "critical";
}

export default function GitHubPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [repoData, setRepoData] = useState<GitHubImportResponse | null>(null);
  const [health, setHealth] = useState<RepoHealthResponse | null>(null);
  const [fileReview, setFileReview] = useState<{ path: string; result: ReviewResponse } | null>(null);
  const [loading, setLoading] = useState<"import" | "health" | string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleImport(e: React.FormEvent) {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setLoading("import");
    setError(null);
    setRepoData(null);
    setHealth(null);
    setFileReview(null);
    try {
      const data = await importGitHubRepo(repoUrl);
      setRepoData(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't import that repo.");
    } finally {
      setLoading(null);
    }
  }

  async function handleHealthScore() {
    setLoading("health");
    setError(null);
    try {
      const data = await getRepoHealthScore(repoUrl);
      setHealth(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't compute a health score.");
    } finally {
      setLoading(null);
    }
  }

  async function handleReviewFile(path: string) {
    setLoading(path);
    setError(null);
    try {
      const result = await reviewGitHubFile(repoUrl, path);
      setFileReview({ path, result });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't review that file.");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div>
      <h1 className="mb-1 font-display text-2xl font-semibold tracking-tight">GitHub</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Connect a public repository, review files individually, or score the whole repo's health.
      </p>

      <form onSubmit={handleImport} className="mb-6 flex gap-2">
        <input
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          className="flex-1 rounded-xl border border-border bg-muted px-4 py-2.5 text-sm outline-none placeholder:text-muted-foreground transition-colors focus:border-primary focus:ring-1 focus:ring-primary/40"
        />
        <Button type="submit" disabled={loading === "import"}>
          {loading === "import" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Github className="h-4 w-4" />}
          Connect
        </Button>
      </form>

      {error && (
        <Card className="mb-6 border-red-500/30">
          <CardContent className="p-4 text-sm text-red-400">{error}</CardContent>
        </Card>
      )}

      {repoData && (
        <>
          <Card className="mb-6">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <h2 className="font-medium">{repoData.owner}/{repoData.repo}</h2>
                {repoData.description && (
                  <p className="text-sm text-muted-foreground">{repoData.description}</p>
                )}
              </div>
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Star className="h-4 w-4" /> {repoData.stars}
                </span>
                <Button size="sm" variant="outline" onClick={handleHealthScore} disabled={loading === "health"}>
                  {loading === "health" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Gauge className="h-4 w-4" />}
                  Repo Health Score
                </Button>
              </div>
            </CardContent>
          </Card>

          {health && (
            <Card className="mb-6">
              <CardContent className="p-5">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="font-medium">Repository health</h3>
                  <span className="text-3xl font-semibold">{health.average_score}<span className="text-sm text-muted-foreground">/100</span></span>
                </div>
                <p className="mb-3 text-xs text-muted-foreground">
                  Based on {health.files_analyzed} analyzed file{health.files_analyzed === 1 ? "" : "s"}. Riskiest files:
                </p>
                <div className="space-y-2">
                  {health.risky_files.map((f) => (
                    <div key={f.path} className="flex items-center justify-between rounded-xl bg-muted p-3 text-sm">
                      <span className="font-mono text-xs">{f.path}</span>
                      <div className="flex items-center gap-2">
                        {f.top_issue && <span className="text-xs text-muted-foreground">{f.top_issue}</span>}
                        <Badge tone={severityTone(f.score)}>{f.score}/100</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="mb-6">
            <CardContent className="p-5">
              <h3 className="mb-3 font-medium">Reviewable files ({repoData.files.length})</h3>
              <div className="space-y-2">
                {repoData.files.map((f) => (
                  <div key={f.path} className="flex items-center justify-between rounded-xl bg-muted p-3">
                    <div className="flex items-center gap-2 text-sm">
                      <FileCode className="h-4 w-4 text-muted-foreground" />
                      <span className="font-mono text-xs">{f.path}</span>
                      <Badge className="capitalize">{f.language}</Badge>
                    </div>
                    <Button size="sm" variant="ghost" onClick={() => handleReviewFile(f.path)} disabled={loading === f.path}>
                      {loading === f.path ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanSearch className="h-4 w-4" />}
                      Review
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {fileReview && (
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-3 font-medium font-mono text-sm">{fileReview.path}</h3>
            {fileReview.result.scores && (
              <p className="mb-3 text-sm text-muted-foreground">
                Overall score: <span className="text-foreground font-medium">{fileReview.result.scores.overall}/100</span>
              </p>
            )}
            {fileReview.result.summary && <p className="mb-3 text-sm">{fileReview.result.summary}</p>}
            {fileReview.result.weaknesses.length > 0 && (
              <ul className="space-y-1 text-xs text-muted-foreground">
                {fileReview.result.weaknesses.map((w, i) => <li key={i}>• {w}</li>)}
              </ul>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
