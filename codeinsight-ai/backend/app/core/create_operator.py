"""Create a password account from an authenticated deployment shell."""

import argparse
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User
from app.schemas.auth import SignupRequest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    args = parser.parse_args()
    password = getpass("Password: ")
    if password != getpass("Confirm password: "):
        parser.exit(1, "Passwords do not match\n")
    try:
        payload = SignupRequest(email=args.email, password=password)
    except ValidationError:
        parser.exit(1, "Enter a valid email and a password of at least eight characters\n")
    if len(password.encode("utf-8")) > 72:
        parser.exit(1, "Password exceeds 72 UTF-8 bytes\n")
    try:
        with SessionLocal.begin() as db:
            user = User(email=payload.email, hashed_password=hash_password(password))
            db.add(user)
            db.flush()
            user_id = user.id
    except IntegrityError:
        parser.exit(1, "An account with that email already exists\n")
    print(f"Operator created: {user_id}")


if __name__ == "__main__":
    main()
