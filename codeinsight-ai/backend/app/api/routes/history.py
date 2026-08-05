from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewHistoryItem, ReviewResponse
from app.services.pdf_service import build_review_pdf

router = APIRouter(tags=["history"])


@router.get("/history", response_model=list[ReviewHistoryItem])
def get_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = ReviewRepository(db)
    return repo.list_recent(user.id)


@router.get("/history/{review_id}", response_model=ReviewResponse)
def get_review(review_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = ReviewRepository(db)
    review = repo.get(review_id, user.id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    result = review.results or {}
    return ReviewResponse(
        id=review.id,
        language=review.language,
        review_type=review.review_type,
        scores=result.get("scores"),
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
        complexity=result if review.review_type == "complexity" else None,
        refactored_code=result.get("refactored_code"),
        explanation=result.get("explanation"),
        unit_tests=result.get("unit_tests"),
        created_at=review.created_at,
    )


@router.get("/history/{review_id}/pdf")
def export_review_pdf(review_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = ReviewRepository(db)
    review = repo.get(review_id, user.id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    pdf_bytes = build_review_pdf(review)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="codeinsight-review-{review_id}.pdf"'},
    )


@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = ReviewRepository(db)
    return repo.analytics_summary(user.id)
