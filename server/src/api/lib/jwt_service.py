from datetime import datetime, timedelta, timezone
from uuid import UUID
from src.config import Config
from src.api.utils import now_utc
from fastapi import HTTPException, status
from src.api.schemas import payloadToken
import jwt


class JWTService:
    """Handle JWT token generation and verification"""

    ALGORITHM = "HS256"

    def __init__(self) -> None:
        self.access_secret: str = Config.JWT_SECRET
        self.refresh_secret: str = Config.JWT_REFRESH_SECRET
        self.access_expire_minutes: int = Config.ACCESS_EXPIRE_MINUTES
        self.refresh_expire_days: int = Config.REFRESH_EXPIRE_DAYS

    def _create_payload(self, user_id: UUID, session_id: UUID, expire_delta: timedelta):
        now: datetime = now_utc()
        expire = now + expire_delta

        return {
            "user_id": str(user_id),
            "session_id": str(session_id),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

    def create_access_token(self, user_id: UUID, session_id: UUID) -> str:
        """Generate short-lived access token."""
        payload = self._create_payload(
            user_id=user_id,
            session_id=session_id,
            expire_delta=timedelta(minutes=self.access_expire_minutes),
        )
        return jwt.encode(payload, self.access_secret, algorithm=self.ALGORITHM)

    def generate_refresh_token(self, user_id: UUID, session_id: UUID) -> str:
        """Generate long-lived refresh token."""
        payload = self._create_payload(
            user_id=user_id,
            session_id=session_id,
            expire_delta=timedelta(days=self.refresh_expire_days),
        )
        return jwt.encode(payload, self.refresh_secret, algorithm=self.ALGORITHM)

    def decode_token(self, token: str, *, is_refresh: bool = False) -> payloadToken:
        """Decode and validate a JWT (access or refresh)."""
        secret = self.refresh_secret if is_refresh else self.access_secret
        try:
            return jwt.decode(token, secret, algorithms=[self.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWKError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or malformed token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_expiry_datetime(self, token: str, *, is_refresh: bool = False) -> datetime:
        """Extract expiration timestamp as datetime."""
        decoded = self.decode_token(token, is_refresh=is_refresh)
        return datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    def verify_token_pair(self, access_token: str, refresh_token: str) -> bool:
        """Ensure both tokens belong to the same session and user."""
        access_data = self.decode_token(access_token)
        refresh_data = self.decode_token(refresh_token, is_refresh=True)

        return (
            access_data["user_id"] == refresh_data["user_id"]
            and access_data["session_id"] == refresh_data["session_id"]
        )
