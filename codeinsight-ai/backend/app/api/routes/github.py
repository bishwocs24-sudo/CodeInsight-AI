from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.github import (
    GitHubFile,
    GitHubFileReviewRequest,
    GitHubImportRequest,
    GitHubImportResponse,
    RepoHealthResponse,
    RiskyFile,
)
from app.schemas.review import ReviewResponse
from app.services.ai_service import AIService, AIServiceError
from app.services.github_service import GitHubService, GitHubServiceError, parse_repo_url

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/import", response_model=GitHubImportResponse)
def import_repo(payload: GitHubImportRequest, user: User = Depends(get_current_user)):
    try:
        owner, repo = parse_repo_url(payload.repo_url)
        gh = GitHubService()
        info = gh.get_repo_info(owner, repo)
        files = gh.list_reviewable_files(owner, repo, info["default_branch"])
    except GitHubServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return GitHubImportResponse(
        owner=owner,
        repo=repo,
        description=info.get("description"),
        stars=info.get("stargazers_count", 0),
        default_branch=info["default_branch"],
        files=[GitHubFile(**f) for f in files],
    )


@router.post("/review-file", response_model=ReviewResponse)
def review_github_file(
    payload: GitHubFileReviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        owner, repo = parse_repo_url(payload.repo_url)
        gh = GitHubService()
        info = gh.get_repo_info(owner, repo)
        files = gh.list_reviewable_files(owner, repo, info["default_branch"], limit=1000)
        match = next((f for f in files if f["path"] == payload.path), None)
        if not match:
            raise HTTPException(status_code=404, detail="File not found or not reviewable.")
        content = gh.get_file_content(owner, repo, payload.path)
    except GitHubServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        ai_service = AIService()
        result = ai_service.analyze("review", match["language"], content)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    scores = result.get("scores")
    repo_db = ReviewRepository(db)
    review = repo_db.create(
        user_id=user.id,
        language=match["language"],
        source_code=content,
        review_type="review",
        overall_score=scores.get("overall") if scores else None,
        results=result,
    )

    return ReviewResponse(
        id=review.id,
        language=review.language,
        review_type=review.review_type,
        scores=scores,
        summary=result.get("summary"),
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
        bugs=result.get("bugs", []),
        security_issues=result.get("security_issues", []),
        code_smells=result.get("code_smells", []),
        best_practices=result.get("best_practices", []),
        naming_suggestions=result.get("naming_suggestions", []),
        performance_suggestions=result.get("performance_suggestions", []),
        memory_suggestions=result.get("memory_suggestions", []),
        edge_cases=result.get("edge_cases", []),
        complexity=None,
        refactored_code=None,
        explanation=None,
        unit_tests=None,
        created_at=review.created_at,
    )


@router.post("/health-score", response_model=RepoHealthResponse)
def repo_health_score(payload: GitHubImportRequest, user: User = Depends(get_current_user)):
    """
    Reviews up to 8 files in the repo and aggregates an overall health
    score. This makes several AI calls, so it's the slowest endpoint -
    the frontend should show a clear loading state.
    """
    try:
        owner, repo = parse_repo_url(payload.repo_url)
        gh = GitHubService()
        info = gh.get_repo_info(owner, repo)
        files = gh.list_reviewable_files(owner, repo, info["default_branch"], limit=8)
    except GitHubServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not files:
        raise HTTPException(status_code=400, detail="No reviewable source files found in this repo.")

    ai_service = AIService()
    scored: list[RiskyFile] = []
    total = 0.0
    analyzed = 0

    for f in files:
        try:
            content = gh.get_file_content(owner, repo, f["path"])
            result = ai_service.analyze("review", f["language"], content)
        except (GitHubServiceError, AIServiceError):
            continue  # skip files that fail to fetch/analyze rather than failing the whole scan

        scores = result.get("scores") or {}
        overall = scores.get("overall", 0)
        weaknesses = result.get("weaknesses") or []
        scored.append(RiskyFile(path=f["path"], score=overall, top_issue=weaknesses[0] if weaknesses else None))
        total += overall
        analyzed += 1

    if analyzed == 0:
        raise HTTPException(status_code=502, detail="Couldn't analyze any files in this repo.")

    risky = sorted(scored, key=lambda r: r.score)[:5]

    return RepoHealthResponse(
        owner=owner,
        repo=repo,
        files_analyzed=analyzed,
        average_score=round(total / analyzed, 1),
        risky_files=risky,
    )
