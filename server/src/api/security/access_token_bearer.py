from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.api.schemas import AuthGuard
from src.api.lib.jwt_service import JWTService
from uuid import UUID


class AccessTokenBearer(HTTPBearer):
    """
    Custom HTTPBearer subclass that extracts and decodes the access token.
    Returns the decoded payload as an AuthGuard model.
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.jwt_service = JWTService()

    async def __call__(self, request: Request) -> AuthGuard:
        creds: HTTPAuthorizationCredentials | None = await super().__call__(request)

        if creds is None or creds.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )

        token = creds.credentials.strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty bearer token",
            )

        # Decode token
        payload = self.jwt_service.decode_token(token, is_refresh=False)
        print(payload)
        return AuthGuard(
            user_id=UUID(payload["user_id"]),
            session_id=UUID(payload["session_id"]),
        )
