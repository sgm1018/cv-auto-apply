"""Security utilities: password hashing and JWT."""
import hashlib
import os
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from smartcvapply.utils.time import utcnow

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def _jti(*, prefix: str, sub: str) -> str:
    """Generate a unique jti with microsecond precision and a random nonce."""
    return hashlib.sha256(
        f"{prefix}-{sub}-{utcnow().timestamp()}-{os.urandom(8).hex()}".encode(),
    ).hexdigest()[:24]


def create_access_token(sub: str, email: str, *, secret: str, ttl_min: int,
                        algorithm: str = "HS256") -> str:
    now = utcnow()
    payload = {
        "sub": sub,
        "email": email,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_min)).timestamp()),
        "jti": _jti(prefix="at", sub=sub),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_refresh_token(sub: str, *, secret: str, ttl_days: int,
                         algorithm: str = "HS256") -> str:
    now = utcnow()
    payload = {
        "sub": sub,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=ttl_days)).timestamp()),
        "jti": _jti(prefix="rt", sub=sub),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithm: str = "HS256") -> dict:
    return jwt.decode(token, secret, algorithms=[algorithm])


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_refresh_token",
    "JWTError",
]
