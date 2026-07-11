import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ebcms.config import get_settings
from ebcms.core.enums import UserRole
from ebcms.models import User

PASSWORD_ITERATIONS = 210_000
JWT_ALGORITHM = "HS256"


class AuthError(ValueError):
    """Raised when credentials or tokens cannot be trusted."""


def ensure_bootstrap_admin(db: Session) -> None:
    settings = get_settings()
    existing_user = db.scalar(
        select(User).where(User.username == settings.bootstrap_admin_username)
    )
    if existing_user:
        return

    db.add(
        User(
            username=settings.bootstrap_admin_username,
            email=settings.bootstrap_admin_email,
            full_name="Bootstrap Administrator",
            role=UserRole.ADMIN.value,
            password_hash=hash_password(settings.bootstrap_admin_password),
            is_active=True,
        )
    )
    db.commit()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_digest = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user.username,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
    }
    return encode_jwt(payload, settings.auth_secret_key)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = decode_jwt(token, settings.auth_secret_key)
    expires_at = payload.get("exp")
    subject = payload.get("sub")
    role = payload.get("role")

    if not subject or not role:
        raise AuthError("Invalid token payload.")
    if not isinstance(expires_at, int) or expires_at < int(datetime.now(UTC).timestamp()):
        raise AuthError("Token has expired.")

    return payload


def encode_jwt(payload: dict[str, Any], secret_key: str) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_part = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        secret_key.encode("utf-8"),
        f"{header_part}.{payload_part}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{header_part}.{payload_part}.{_base64url_encode(signature)}"


def decode_jwt(token: str, secret_key: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
    except ValueError as exc:
        raise AuthError("Malformed token.") from exc

    expected_signature = hmac.new(
        secret_key.encode("utf-8"),
        f"{header_part}.{payload_part}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(_base64url_encode(expected_signature), signature_part):
        raise AuthError("Invalid token signature.")

    header = json.loads(_base64url_decode(header_part))
    if header.get("alg") != JWT_ALGORITHM:
        raise AuthError("Unsupported token algorithm.")

    return json.loads(_base64url_decode(payload_part))


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")
