"""
Repository layer - the only place that issues SQLAlchemy queries for
Reviews. Every method is scoped by user_id so one user never sees
another's data.
"""
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: Session):
        self._db = db

    def create(
        self,
        *,
        user_id: str,
        language: str,
        source_code: str,
        review_type: str,
        overall_score: float | None,
        results: dict,
    ) -> Review:
        review = Review(
            user_id=user_id,
            language=language,
            source_code=source_code,
            review_type=review_type,
            overall_score=overall_score,
            results=results,
        )
        self._db.add(review)
        self._db.commit()
        self._db.refresh(review)
        return review

    def get(self, review_id: str, user_id: str) -> Review | None:
        review = self._db.get(Review, review_id)
        if review is None or review.user_id != user_id:
            return None
        return review

    def list_recent(self, user_id: str, limit: int = 50) -> list[Review]:
        return (
            self._db.query(Review)
            .filter(Review.user_id == user_id)
            .order_by(desc(Review.created_at))
            .limit(limit)
            .all()
        )

    def analytics_summary(self, user_id: str) -> dict:
        reviews = self._db.query(Review).filter(Review.user_id == user_id).all()
        total = len(reviews)
        scored = [r.overall_score for r in reviews if r.overall_score is not None]
        avg_score = round(sum(scored) / len(scored), 1) if scored else None

        by_language: dict[str, int] = {}
        for r in reviews:
            by_language[r.language] = by_language.get(r.language, 0) + 1
        most_reviewed_language = (
            max(by_language, key=by_language.get) if by_language else None
        )

        return {
            "reviews_completed": total,
            "average_score": avg_score,
            "most_reviewed_language": most_reviewed_language,
            "reviews_by_language": by_language,
        }

    def delete_all_for_user(self, user_id: str) -> None:
        self._db.query(Review).filter(Review.user_id == user_id).delete()
        self._db.commit()
