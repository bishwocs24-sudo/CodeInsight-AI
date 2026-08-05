from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_current_user
from app.models.user import User
from app.services.github_service import EXT_TO_LANGUAGE

router = APIRouter(tags=["upload"])

MAX_UPLOAD_BYTES = 500_000  # 500KB - generous for a single source file


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    name = file.filename or ""
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    language = EXT_TO_LANGUAGE.get(ext)
    if not language:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Upload a source file in a supported language.",
        )

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 500KB).")

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File isn't valid UTF-8 text.") from exc

    return {"filename": name, "language": language, "code": content}
