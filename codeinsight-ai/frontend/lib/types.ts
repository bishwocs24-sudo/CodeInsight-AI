export type Language =
  | "python"
  | "java"
  | "javascript"
  | "typescript"
  | "go"
  | "rust"
  | "c"
  | "cpp"
  | "csharp"
  | "kotlin"
  | "swift"
  | "ruby"
  | "php";

export type ReviewType =
  | "review"
  | "refactor"
  | "security"
  | "explain"
  | "tests"
  | "complexity";

export interface ReviewScores {
  overall: number;
  readability: number;
  performance: number;
  maintainability: number;
  security: number;
  documentation: number;
  code_quality: number;
}

export interface BugFinding {
  description: string;
  line?: number | null;
  severity: "low" | "medium" | "high" | "critical";
}

export interface SecurityIssue {
  title: string;
  description: string;
  line?: number | null;
  severity: "low" | "medium" | "high" | "critical";
  cwe?: string | null;
  remediation: string;
}

export interface ReviewResponse {
  id: string;
  language: string;
  review_type: ReviewType;
  scores: ReviewScores | null;
  summary: string | null;
  strengths: string[];
  weaknesses: string[];
  bugs: BugFinding[];
  security_issues: SecurityIssue[];
  code_smells: string[];
  best_practices: string[];
  naming_suggestions: string[];
  performance_suggestions: string[];
  memory_suggestions: string[];
  edge_cases: string[];
  complexity: Record<string, unknown> | null;
  refactored_code: string | null;
  explanation: string | null;
  unit_tests: string | null;
  created_at: string;
}

export interface ReviewHistoryItem {
  id: string;
  language: string;
  review_type: ReviewType;
  overall_score: number | null;
  created_at: string;
}

export interface AnalyticsSummary {
  reviews_completed: number;
  average_score: number | null;
  most_reviewed_language: string | null;
  reviews_by_language: Record<string, number>;
}

export interface AppUser {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AppUser;
}

export interface GitHubFile {
  path: string;
  language: string;
  size: number;
}

export interface GitHubImportResponse {
  owner: string;
  repo: string;
  description: string | null;
  stars: number;
  default_branch: string;
  files: GitHubFile[];
}

export interface RiskyFile {
  path: string;
  score: number;
  top_issue: string | null;
}

export interface RepoHealthResponse {
  owner: string;
  repo: string;
  files_analyzed: number;
  average_score: number;
  risky_files: RiskyFile[];
}

export interface AppSettings {
  dark_mode: boolean;
  email_notifications: boolean;
  preferred_ai_model: string;
  preferred_language: string;
}

export const LANGUAGES: { value: Language; label: string }[] = [
  { value: "python", label: "Python" },
  { value: "java", label: "Java" },
  { value: "javascript", label: "JavaScript" },
  { value: "typescript", label: "TypeScript" },
  { value: "go", label: "Go" },
  { value: "rust", label: "Rust" },
  { value: "c", label: "C" },
  { value: "cpp", label: "C++" },
  { value: "csharp", label: "C#" },
  { value: "kotlin", label: "Kotlin" },
  { value: "swift", label: "Swift" },
  { value: "ruby", label: "Ruby" },
  { value: "php", label: "PHP" },
];
