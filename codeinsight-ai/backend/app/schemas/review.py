from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SUPPORTED_LANGUAGES = Literal[
    "python", "java", "javascript", "typescript", "go", "rust",
    "c", "cpp", "csharp", "kotlin", "swift", "ruby", "php",
]

ReviewType = Literal["review", "refactor", "security", "explain", "tests", "complexity"]


class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50_000)
    language: SUPPORTED_LANGUAGES
    review_type: ReviewType = "review"


class ReviewScores(BaseModel):
    overall: float
    readability: float
    performance: float
    maintainability: float
    security: float
    documentation: float
    code_quality: float


class ReviewResponse(BaseModel):
    id: str
    language: str
    review_type: str
    scores: ReviewScores | None = None
    summary: str | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    bugs: list[dict[str, Any]] = []
    security_issues: list[dict[str, Any]] = []
    code_smells: list[str] = []
    best_practices: list[str] = []
    naming_suggestions: list[str] = []
    performance_suggestions: list[str] = []
    memory_suggestions: list[str] = []
    edge_cases: list[str] = []
    complexity: dict[str, Any] | None = None
    refactored_code: str | None = None
    explanation: str | None = None
    unit_tests: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewHistoryItem(BaseModel):
    id: str
    language: str
    review_type: str
    overall_score: float | None
    created_at: datetime

    class Config:
        from_attributes = True
