import uuid
from datetime import timedelta

import jwt
import pytest

from app.core.exceptions import (
    AuthenticationException,
    InvalidTokenException,
    RateLimitExceededException,
    TokenExpiredException,
)
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.security import (
    ANONYMOUS,
    BearerTokenAuthenticator,
    TokenService,
    bearer_token,
    hash_password,
    verify_password,
)

SECRET = "s" * 40


def _tokens(ttl: timedelta = timedelta(minutes=5)) -> TokenService:
    return TokenService(SECRET, ttl)


def test_password_hash_verifies_only_the_right_password() -> None:
    stored = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", stored)
    assert not verify_password("correct horse battery stapl", stored)
    assert "correct horse" not in stored
    assert stored.startswith("scrypt$")


def test_hashes_are_salted() -> None:
    assert hash_password("same password") != hash_password("same password")


@pytest.mark.parametrize("stored", ["", "!", "plaintext", "scrypt$1$2", "md5$1$1$1$AAAA$AAAA"])
def test_malformed_or_foreign_hashes_never_verify(stored: str) -> None:
    assert not verify_password("anything", stored)


def test_token_round_trip() -> None:
    user_id = uuid.uuid4()

    assert _tokens().verify(_tokens().issue(user_id)) == user_id


def test_expired_token_is_reported_as_expired() -> None:
    token = _tokens(timedelta(seconds=-1)).issue(uuid.uuid4())

    with pytest.raises(TokenExpiredException) as error:
        _tokens().verify(token)

    assert error.value.code == "TOKEN_EXPIRED"
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize(
    "token",
    [
        "not-a-token",
        TokenService("another-secret" * 4, timedelta(minutes=5)).issue(uuid.uuid4()),
        jwt.encode({"sub": str(uuid.uuid4())}, SECRET, algorithm="HS256"),  # no expiry
        jwt.encode({"sub": "not-a-uuid", "exp": 9999999999, "iat": 0}, SECRET, algorithm="HS256"),
        jwt.encode({"sub": str(uuid.uuid4()), "exp": 9999999999, "iat": 0}, "", algorithm="none"),
    ],
    ids=["garbage", "wrong-key", "no-expiry", "bad-subject", "unsigned"],
)
def test_invalid_tokens_are_rejected(token: str) -> None:
    with pytest.raises(InvalidTokenException):
        _tokens().verify(token)


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("Bearer abc", "abc"),
        ("bearer abc", "abc"),
        ("Basic abc", None),
        ("Bearer ", None),
        ("", None),
    ],
)
def test_bearer_token_extraction(header: str, expected: str | None) -> None:
    assert bearer_token({"authorization": header}) == expected


async def test_authenticator_requires_a_token_unless_anonymous_access_is_allowed() -> None:
    user_id = uuid.uuid4()
    headers = {"authorization": f"Bearer {_tokens().issue(user_id)}"}

    strict = BearerTokenAuthenticator(_tokens(), required=True)
    lenient = BearerTokenAuthenticator(_tokens(), required=False)

    assert (await strict.authenticate(headers)).user_id == user_id
    with pytest.raises(AuthenticationException):
        await strict.authenticate({})
    assert await lenient.authenticate({}) is ANONYMOUS
    with pytest.raises(InvalidTokenException):
        await lenient.authenticate({"authorization": "Bearer forged"})


async def test_rate_limiter_allows_the_budget_then_blocks_until_the_window_moves() -> None:
    now = [100.0]
    limiter = SlidingWindowRateLimiter(3, window_seconds=60, clock=lambda: now[0])

    for _ in range(3):
        await limiter.check("user:1")
    with pytest.raises(RateLimitExceededException) as error:
        await limiter.check("user:1")
    await limiter.check("user:2")  # budgets are per caller

    assert error.value.retry_after_seconds == 60
    assert error.value.headers == {"Retry-After": "60"}

    now[0] += 45
    with pytest.raises(RateLimitExceededException) as later:
        await limiter.check("user:1")
    assert later.value.retry_after_seconds == 15

    now[0] += 16
    await limiter.check("user:1")


async def test_a_limit_of_zero_disables_the_limiter() -> None:
    limiter = SlidingWindowRateLimiter(0)

    for _ in range(1000):
        await limiter.check("anyone")
