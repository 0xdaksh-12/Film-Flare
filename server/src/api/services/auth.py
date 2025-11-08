from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID
from datetime import datetime, timezone

from src.core import get_session
from src.config import Config
from src.api.lib import JWTService, PasswordService
from src.api.models import Session, User, UserAuth
import src.api.schemas as AuthSchema
import logging

logger = logging.getLogger("auth")


class AuthService:
    """Manages user registration, authentication, and session lifecycle."""

    def __init__(
        self,
        session: AsyncSession = Depends(get_session),
        jwt_service: JWTService = Depends(JWTService),
        password_service: PasswordService = Depends(PasswordService),
    ) -> None:
        self.session = session
        self.jwt_service = jwt_service
        self.password_service = password_service
        self.cookie_token = Config.COOKIE_TOKEN

    async def register(
        self, data: AuthSchema.RegisterData, response: Response
    ) -> AuthSchema.AuthResponse:
        """Register a new user and create initial session."""

        try:
            # Check for existing User
            email = data.email
            existing_user = await self.session.scalar(
                select(UserAuth).where(UserAuth.email == email)
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already exists",
                )

            # Create User and related UserAuth
            hashed_password = self.password_service.hashed(data.password)
            user = User(name=data.name)
            self.session.add(user)
            await self.session.flush()  # Generate user.id

            user_auth = UserAuth(
                email=data.email,
                password_hash=hashed_password,
                user_id=user.id,
                provider=AuthSchema.AuthProvider.EMAIL,
            )
            self.session.add(user_auth)

            # Create Session
            session_obj = await self._create_session(user.id, data)

            # Generate tokens
            access_token, refresh_token = self._generate_token_pair(
                user.id, session_obj.id
            )

            # Save hashed refresh token in DB
            session_obj.refresh_token_hash = self.password_service.hashed(refresh_token)

            # Commit DB changes
            await self.session.commit()

            # Set cookie
            self._set_cookie_token(response, refresh_token)

            logger.info(f"[REGISTER] User registered successfully: {user.name}")
            return AuthSchema.AuthResponse(success=True, accessToken=access_token)

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.exception("Registration failed: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error")

    async def login_user(
        self, data: AuthSchema.LoginData, response: Response
    ) -> AuthSchema.AuthResponse:
        """Authenticate existing user and create a new session."""
        try:
            user_auth = await self.session.scalar(
                select(UserAuth).where(UserAuth.email == data.email)
            )
            if not user_auth:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            user = await self.session.scalar(
                select(User).filter_by(id=user_auth.user_id)
            )
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Email/password validation
            if not user_auth.password_hash or not self.password_service.compareHash(
                data.password, user_auth.password_hash
            ):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Create new session
            session_obj = await self._create_session(user.id, data)

            # Generate tokens
            access_token, refresh_token = self._generate_token_pair(
                user.id, session_obj.id
            )

            # Store hashed refresh token
            session_obj.refresh_token_hash = self.password_service.hashed(refresh_token)
            await self.session.commit()

            # Set refresh cookie
            self._set_cookie_token(response, refresh_token)

            logger.info(f"[LOGIN] User logged in successfully: {user.name}")
            return AuthSchema.AuthResponse(success=True, accessToken=access_token)

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.exception("Login failed: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error")

    async def logout_user(self, auth_data: AuthSchema.AuthGuard, response: Response):
        """Invalidate the current session and clear cookie."""
        try:
            session_id = auth_data.session_id
            session_obj = await self.session.execute(
                select(Session).where(Session.id == session_id, Session.valid == True)
            )

            session_obj = session_obj.scalars().one_or_none()

            if not session_obj:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session",
                )

            session_obj.valid = False
            await self.session.commit()

            self._delete_cookie_token(response)
            logger.info(f"[LOGOUT] Session invalidated: {session_id}")

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.exception("Logout failed: %s", e)
            raise HTTPException(status_code=500, detail="Logout failed")

    async def refresh_token(
        self, refresh_token: str, response: Response
    ) -> AuthSchema.AuthResponse:
        """Rotate refresh token and issue a new access token."""
        try:
            payload: AuthSchema.payloadToken = self.jwt_service.decode_token(
                refresh_token, is_refresh=True
            )
            user_id = UUID(payload["user_id"])
            session_id = UUID(payload["session_id"])

            # Fetch session
            session_obj = await self.session.execute(
                select(Session).where(Session.id == session_id, Session.valid == True)
            )

            session_obj = session_obj.scalars().one_or_none()

            if not session_obj or not session_obj.refresh_token_hash:
                raise HTTPException(status_code=401, detail="Invalid session")

            # Verify stored refresh hash
            if not self.password_service.compareHash(
                refresh_token, session_obj.refresh_token_hash
            ):
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            # Generate new access token
            access_token = self.jwt_service.create_access_token(user_id, session_id)

            # Rotate refresh token if near expiry
            if await self._should_rotate_refresh_token(payload):
                new_refresh_token = self.jwt_service.generate_refresh_token(
                    user_id, session_id
                )
                session_obj.refresh_token_hash = self.password_service.hashed(
                    new_refresh_token
                )
                self._set_cookie_token(response, new_refresh_token)
                logger.info(
                    f"[REFRESH] Rotated refresh token for session: {session_id}"
                )

            await self.session.commit()
            return AuthSchema.AuthResponse(success=True, accessToken=access_token)

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.exception("Token refresh failed: %s", e)
            raise HTTPException(status_code=500, detail="Token refresh failed")

    async def _create_session(
        self, user_id: UUID, data: AuthSchema.ClientMeta
    ) -> Session:
        """Create a new user session record."""
        session_obj = Session(
            user_id=user_id,
            user_agent=data.user_agent,
            ip_address=data.ip_address,
        )
        self.session.add(session_obj)
        await self.session.flush()
        return session_obj

    def _generate_token_pair(self, user_id: UUID, session_id: UUID) -> tuple[str, str]:
        """Generate both access and refresh tokens."""
        access_token = self.jwt_service.create_access_token(user_id, session_id)
        refresh_token = self.jwt_service.generate_refresh_token(user_id, session_id)
        return access_token, refresh_token

    async def _should_rotate_refresh_token(
        self, payload: AuthSchema.payloadToken
    ) -> bool:
        """Return True if refresh token has used 75% of its lifetime."""
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        lifetime = (exp - iat).total_seconds()
        elapsed = (datetime.now(timezone.utc) - iat).total_seconds()
        return elapsed >= lifetime * 0.75

    def _set_cookie_token(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=self.cookie_token,
            value=token,
            httponly=True,
            samesite="none" if Config.is_production else "lax",
            secure=Config.is_production,
            path="/auth",
            max_age=7 * 24 * 60 * 60,  # 7 days
        )

    def _delete_cookie_token(self, response: Response) -> None:
        response.delete_cookie(
            key=self.cookie_token,
            path="/auth",
            httponly=True,
            samesite="none" if Config.is_production else "lax",
            secure=Config.is_production,
        )
