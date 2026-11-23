"""Independent static-analysis API; does not require an LLM API key."""
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.review import ReviewRequest
from app.services.static_analysis import analyze_static

router = APIRouter(prefix='/analysis', tags=['static-analysis'])

@router.post('/static')
def static_scan(payload: ReviewRequest, user: User = Depends(get_current_user)):
    return analyze_static(payload.language, payload.code)
