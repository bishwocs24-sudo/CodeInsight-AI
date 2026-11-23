import type {
  AnalyticsSummary,
  AppSettings,
  AppUser,
  AuthResponse,
  GitHubImportResponse,
  Language,
  RepoHealthResponse,
  ReviewHistoryItem,
  ReviewResponse,
  ReviewType,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "codeinsight:token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = typeof body.detail === "string" ? body.detail
      : Array.isArray(body.detail) ? body.detail.map((item: { msg: string }) => item.msg).join(". ")
      : `Request failed (${res.status})`;
    throw new ApiError(message, res.status);
  }
  return res.json() as Promise<T>;
}

export function signup(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export type AuthOptions = { signup: boolean; github: boolean };

export function getAuthOptions(): Promise<AuthOptions> {
  return request<AuthOptions>("/auth/options");
}

export function getMe(): Promise<AppUser> {
  return request<AppUser>("/auth/me");
}

export function runAnalysis(
  reviewType: ReviewType,
  code: string,
  language: Language
): Promise<ReviewResponse> {
  const endpoint = `/${reviewType === "review" ? "review" : reviewType}`;
  return request<ReviewResponse>(endpoint, {
    method: "POST",
    body: JSON.stringify({ code, language, review_type: reviewType }),
  });
}

export function getHistory(): Promise<ReviewHistoryItem[]> {
  return request<ReviewHistoryItem[]>("/history");
}

export function getReview(id: string): Promise<ReviewResponse> {
  return request<ReviewResponse>(`/history/${id}`);
}

export function getAnalytics(): Promise<AnalyticsSummary> {
  return request<AnalyticsSummary>("/analytics");
}

export function importGitHubRepo(repoUrl: string): Promise<GitHubImportResponse> {
  return request<GitHubImportResponse>("/github/import", {
    method: "POST",
    body: JSON.stringify({ repo_url: repoUrl }),
  });
}

export function reviewGitHubFile(repoUrl: string, path: string): Promise<ReviewResponse> {
  return request<ReviewResponse>("/github/review-file", {
    method: "POST",
    body: JSON.stringify({ repo_url: repoUrl, path }),
  });
}

export function getRepoHealthScore(repoUrl: string): Promise<RepoHealthResponse> {
  return request<RepoHealthResponse>("/github/health-score", {
    method: "POST",
    body: JSON.stringify({ repo_url: repoUrl }),
  });
}

export function getSettings(): Promise<AppSettings> {
  return request<AppSettings>("/settings");
}

export function updateSettings(patch: Partial<AppSettings>): Promise<AppSettings> {
  return request<AppSettings>("/settings", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export async function deleteAccount(): Promise<void> {
  await request("/account", { method: "DELETE" });
}

export async function uploadCodeFile(
  file: File
): Promise<{ filename: string; language: Language; code: string }> {
  const form = new FormData();
  form.append("file", file);
  const token = getToken();
  const res = await fetch(`${API_URL}/upload`, {
    method: "POST",
    body: form,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail ?? `Upload failed (${res.status})`, res.status);
  }
  return res.json();
}

export async function downloadReviewPdf(reviewId: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_URL}/history/${reviewId}/pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) {
    throw new ApiError("Couldn't generate the PDF.", res.status);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `codeinsight-review-${reviewId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}

export { ApiError };

export type JobStatus = "queued" | "running" | "publishing" | "completed" | "failed" | "cancelled" | "superseded";
export type FindingVerdict = "confirmed" | "false_positive" | "clear";

export interface AutomationFinding {
  id: number;
  source: "semgrep" | "static" | "ai";
  rule_id: string;
  path: string;
  line: number;
  severity: "high" | "medium" | "low";
  message: string;
  evidence_sha256: string;
  suppressed: boolean;
  verdict: FindingVerdict | null;
}

export interface AutomationJob {
  id: string;
  status: JobStatus;
  attempts: number;
  created_at: string;
  updated_at: string;
  repository: string | null;
  pull_number: number | null;
  head_sha: string | null;
  error: string | null;
  result: {
    files_reviewed: number;
    files_skipped: number;
    semgrep: string;
    ai: string;
    ruleset: string;
    duration_ms: number;
    verification?: { status: string };
    publication?: string;
    findings_truncated: boolean;
  } | null;
}

export type AutomationJobDetail = AutomationJob & { findings: AutomationFinding[] };

export const getAutomationJobs = () => request<AutomationJob[]>("/automation/jobs");
export const getAutomationJob = (id: string) => request<AutomationJobDetail>(`/automation/jobs/${id}`);
export const getAutomationCapabilities = () => request<{ sandbox: boolean; ai: boolean }>("/automation/capabilities");

export function queueReview(language: string, code: string, tests?: string) {
  return request<{ id: string; status: JobStatus }>("/automation/jobs", {
    method: "POST", body: JSON.stringify({ language, code, tests }),
  });
}

export function cancelAutomationJob(id: string) {
  return request(`/automation/jobs/${id}/cancel`, { method: "POST" });
}

export function submitFindingFeedback(job: string, finding: number, verdict: FindingVerdict) {
  return request(`/automation/jobs/${job}/findings/${finding}/feedback`, {
    method: "PUT", body: JSON.stringify({ verdict }),
  });
}

export async function exportAutomationJob(id: string) {
  const data = await request<unknown>(`/automation/jobs/${id}/sarif`);
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/sarif+json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `codeguard-${id}.sarif`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
