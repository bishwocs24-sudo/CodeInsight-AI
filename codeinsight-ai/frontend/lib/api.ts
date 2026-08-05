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
    throw new ApiError(body.detail ?? `Request failed (${res.status})`, res.status);
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
