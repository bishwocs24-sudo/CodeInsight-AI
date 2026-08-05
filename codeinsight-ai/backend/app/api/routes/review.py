from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.settings import Settings
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewRequest, ReviewResponse
from app.services.ai_service import AIService, AIServiceError

router = APIRouter(tags=["review"])


def _run_analysis(
    review_type: str, payload: ReviewRequest, db: Session, user: User
) -> ReviewResponse:
    user_settings = db.get(Settings, user.id)
    preferred_model = user_settings.preferred_ai_model if user_settings else None

    try:
        ai_service = AIService()
        result = ai_service.analyze(review_type, payload.language, payload.code, model=preferred_model)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    scores = result.get("scores")
    overall_score = scores.get("overall") if scores else None

    repo = ReviewRepository(db)
    review = repo.create(
        user_id=user.id,
        language=payload.language,
        source_code=payload.code,
        review_type=review_type,
        overall_score=overall_score,
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
        complexity=result if review_type == "complexity" else None,
        refactored_code=result.get("refactored_code"),
        explanation=result.get("explanation"),
        unit_tests=result.get("unit_tests"),
        created_at=review.created_at,
    )


@router.post("/review", response_model=ReviewResponse)
def review_code(payload: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _run_analysis("review", payload, db, user)


@router.post("/security", response_model=ReviewResponse)
def security_scan(payload: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _run_analysis("security", payload, db, user)


@router.post("/refactor", response_model=ReviewResponse)
def refactor_code(payload: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _run_analysis("refactor", payload, db, user)


@router.post("/tests", response_model=ReviewResponse)
def generate_tests(payload: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _run_analysis("tests", payload, db, user)


@router.post("/explain", response_model=ReviewResponse)
def explain_code(payload: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _run_analysis("explain", payload, db, user)


@router.post("/complexity", response_model=ReviewResponse)
def analyze_complexity(payload: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _run_analysis("complexity", payload, db, user)
