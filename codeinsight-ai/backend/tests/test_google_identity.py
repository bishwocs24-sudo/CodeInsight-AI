import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.routes.auth import google_exchange
from app.core.config import get_settings
from app.db.database import Base
from app.models.user import User
from app.schemas.auth import GoogleExchangeRequest
from app.services.google_identity import keys


class GoogleExchangeTests(unittest.TestCase):
    def setUp(self):
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.enterContext(patch.object(keys, "get_signing_key_from_jwt",
                                       return_value=SimpleNamespace(key=self.key.public_key())))
        self.enterContext(patch.multiple(get_settings(), auth_google_id="web-client", signup_enabled=True))
        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        self.db = self.enterContext(Session(engine))

    def exchange(self, **overrides):
        now = int(time.time())
        claims = {"sub": "subject1", "email": "member@example.org", "email_verified": True,
                  "exp": now + 3600, "iat": now, "aud": "web-client",
                  "iss": "https://accounts.google.com", **overrides}
        encoded = jwt.encode(claims, self.key, algorithm="RS256")
        return google_exchange(GoogleExchangeRequest(id_token=encoded), self.db)

    def test_repeated_signin_resolves_same_account(self):
        first = self.exchange()
        self.assertEqual(first.user.id, self.exchange().user.id)
        self.assertLessEqual(jwt.decode(first.access_token, options={"verify_signature": False})["exp"],
                             int(time.time()) + 2700)

    def test_reject_wrong_audience_unverified_email_and_expired_token(self):
        for claims in ({"aud": "other-app"}, {"email_verified": False}, {"exp": 0}, {"iss": "other"}):
            with self.subTest(claims=claims), self.assertRaises(HTTPException) as error:
                self.exchange(**claims)
            self.assertEqual(error.exception.status_code, 401)

    def test_protect_existing_account_and_closed_registration(self):
        self.db.add(User(email="member@example.org"))
        self.db.commit()
        with self.assertRaises(HTTPException) as conflict:
            self.exchange()
        self.assertEqual(conflict.exception.status_code, 409)
        with patch.object(get_settings(), "signup_enabled", False), self.assertRaises(HTTPException) as closed:
            self.exchange(email="another@example.org")
        self.assertEqual(closed.exception.status_code, 403)
