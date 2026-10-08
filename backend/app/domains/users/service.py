import asyncio

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    AuthenticationException,
    EmailAlreadyRegisteredException,
    InvalidCredentialsException,
)
from app.core.logging import get_logger
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    Principal,
    TokenService,
    hash_password,
    verify_password,
)
from app.database.unit_of_work import UnitOfWork
from app.domains.users.models import User
from app.domains.users.repository import UserRepository
from app.domains.users.schemas import TokenResponse, UserLogin, UserRead, UserRegister

logger = get_logger(__name__)


class AuthService:
    """Registration, sign-in and "who am I"."""

    def __init__(self, users: UserRepository, tokens: TokenService, uow: UnitOfWork) -> None:
        self._users = users
        self._tokens = tokens
        self._uow = uow

    async def register(self, payload: UserRegister) -> TokenResponse:
        if await self._users.get_by_email(payload.email) is not None:
            raise EmailAlreadyRegisteredException()
        # scrypt is deliberately slow; keep it off the event loop.
        password_hash = await asyncio.to_thread(hash_password, payload.password)
        try:
            user = await self._users.create(email=payload.email, password_hash=password_hash)
            await self._uow.commit()
        except IntegrityError:
            # Two registrations for one email raced; the unique constraint decided.
            await self._uow.rollback()
            raise EmailAlreadyRegisteredException() from None
        logger.info("user_registered")
        return self._token_for(user)

    async def login(self, payload: UserLogin) -> TokenResponse:
        user = await self._users.get_by_email(payload.email)
        stored = user.password_hash if user else DUMMY_PASSWORD_HASH
        valid = await asyncio.to_thread(verify_password, payload.password, stored)
        if user is None or not valid:
            logger.warning("login_failed")
            raise InvalidCredentialsException()
        return self._token_for(user)

    async def current_user(self, principal: Principal) -> User:
        user = await self._users.get(principal.user_id) if principal.user_id else None
        if user is None:
            raise AuthenticationException()
        return user

    def _token_for(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=self._tokens.issue(user.id),
            expires_in=self._tokens.ttl_seconds,
            user=UserRead.model_validate(user),
        )
