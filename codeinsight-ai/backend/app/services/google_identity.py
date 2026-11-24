import jwt
from fastapi import HTTPException

from app.core.config import get_settings

keys = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs", timeout=5)


def verify_identity(encoded: str) -> dict:
    audience = get_settings().auth_google_id.strip()
    if not audience:
        raise HTTPException(503, "Google access is not configured for this backend")
    try:
        key = keys.get_signing_key_from_jwt(encoded)
        claims = jwt.decode(encoded, key.key, algorithms=["RS256"], audience=audience,
                            issuer=["https://accounts.google.com", "accounts.google.com"],
                            options={"require": ["exp", "iat", "sub", "email", "aud", "iss"]})
    except jwt.PyJWKClientConnectionError as exc:
        raise HTTPException(503, "Google verification is temporarily unavailable") from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Invalid Google identity") from exc
    if (claims.get("email_verified") is not True or claims.get("azp", audience) != audience
            or len(claims["sub"]) > 255):
        raise HTTPException(401, "Invalid Google identity")
    return claims
