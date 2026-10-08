"""Security primitives: principals, password hashing, access tokens, secret detection."""

import base64
import hashlib
import hmac
import secrets
import uuid
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import jwt

from app.core.exceptions import (
    AuthenticationException,
    InvalidTokenException,
    TokenExpiredException,
)

SENSITIVE_KEY_PARTS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "passwd",
    "password",
    "private_key",
    "secret",
    "token",
)


# Keys naming a pointer to a secret (e.g. "credentials_ref") are safe to store.
SECRET_REFERENCE_SUFFIXES: tuple[str, ...] = ("_ref", "_reference")


def is_sensitive_key(key: str) -> bool:
    normalised = key.lower().replace("-", "_")
    return any(part in normalised for part in SENSITIVE_KEY_PARTS)


def _is_secret_reference(key: str) -> bool:
    return key.lower().replace("-", "_").endswith(SECRET_REFERENCE_SUFFIXES)


def find_sensitive_keys(value: object, prefix: str = "") -> Iterator[str]:
    """Yield dotted paths of keys that look like they hold a secret value."""
    if isinstance(value, Mapping):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if is_sensitive_key(str(key)) and not _is_secret_reference(str(key)):
                yield path
            yield from find_sensitive_keys(nested, path)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from find_sensitive_keys(nested, f"{prefix}[{index}]")


@dataclass(frozen=True, slots=True)
class Principal:
    """Who a request acts as. ``user_id`` is ``None`` for anonymous requests."""

    user_id: uuid.UUID | None
    is_authenticated: bool


ANONYMOUS = Principal(user_id=None, is_authenticated=False)


# --- Passwords -------------------------------------------------------------------
#
# scrypt from the standard library: memory-hard, salted, no extra dependency.
# Stored format: scrypt$<n>$<r>$<p>$<salt b64>$<hash b64>, so parameters can be
# raised later without invalidating existing hashes.

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1
_SALT_BYTES, _KEY_BYTES = 16, 32
_SCHEME = "scrypt"


def _derive(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=_KEY_BYTES)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = _derive(password, salt, _SCRYPT_N, _SCRYPT_R, _SCRYPT_P)
    encoded = (base64.b64encode(part).decode() for part in (salt, digest))
    return "$".join([_SCHEME, str(_SCRYPT_N), str(_SCRYPT_R), str(_SCRYPT_P), *encoded])


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check of ``password`` against a stored hash. Never raises."""
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != _SCHEME:
            return False
        expected = base64.b64decode(digest)
        actual = _derive(password, base64.b64decode(salt), int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


# Verified when the account does not exist, so a login attempt costs the same
# either way and response time does not reveal which emails are registered.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))


# --- Access tokens ----------------------------------------------------------------

_ALGORITHM = "HS256"


class TokenService:
    """Issues and verifies signed, expiring access tokens (JWT, HS256)."""

    def __init__(self, secret: str, ttl: timedelta) -> None:
        self._secret = secret
        self._ttl = ttl

    @property
    def ttl_seconds(self) -> int:
        return int(self._ttl.total_seconds())

    def issue(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        claims = {"sub": str(user_id), "iat": now, "exp": now + self._ttl}
        return jwt.encode(claims, self._secret, algorithm=_ALGORITHM)

    def verify(self, token: str) -> uuid.UUID:
        """Return the user id a token was issued for, or raise an authentication error."""
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],
                options={"require": ["sub", "exp", "iat"]},
            )
            return uuid.UUID(claims["sub"])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException() from None
        except (jwt.InvalidTokenError, ValueError):
            raise InvalidTokenException() from None


_BEARER_PREFIX = "bearer "


def bearer_token(headers: Mapping[str, str]) -> str | None:
    """The token from an ``Authorization: Bearer <token>`` header, if present."""
    value = headers.get("authorization", "")
    if not value.lower().startswith(_BEARER_PREFIX):
        return None
    return value[len(_BEARER_PREFIX) :].strip() or None


class Authenticator(Protocol):
    async def authenticate(self, headers: Mapping[str, str]) -> Principal:
        """Resolve the caller, raising an ``AuthenticationException`` when rejected."""
        ...


class BearerTokenAuthenticator:
    """Authenticates requests carrying an access token issued by ``TokenService``.

    With ``required=False`` (local development only) a request without a token
    is the anonymous principal; a request with a bad token is still rejected.
    """

    def __init__(self, tokens: TokenService, *, required: bool) -> None:
        self._tokens = tokens
        self._required = required

    async def authenticate(self, headers: Mapping[str, str]) -> Principal:
        token = bearer_token(headers)
        if token is None:
            if self._required:
                raise AuthenticationException()
            return ANONYMOUS
        return Principal(user_id=self._tokens.verify(token), is_authenticated=True)
