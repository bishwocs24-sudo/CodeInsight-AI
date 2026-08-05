from pydantic import BaseModel


class GitHubImportRequest(BaseModel):
    repo_url: str


class GitHubFile(BaseModel):
    path: str
    language: str
    size: int


class GitHubImportResponse(BaseModel):
    owner: str
    repo: str
    description: str | None = None
    stars: int
    default_branch: str
    files: list[GitHubFile]


class GitHubFileReviewRequest(BaseModel):
    repo_url: str
    path: str


class RiskyFile(BaseModel):
    path: str
    score: float
    top_issue: str | None = None


class RepoHealthResponse(BaseModel):
    owner: str
    repo: str
    files_analyzed: int
    average_score: float
    risky_files: list[RiskyFile]
