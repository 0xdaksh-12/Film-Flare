from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID

from src.core import get_session
from src.api.models import User, Session
from src.api.schemas import AuthGuard
from src.api.security.access_token_bearer import AccessTokenBearer


async def auth_guard(
    token_data: AuthGuard = Depends(AccessTokenBearer()),
    db: AsyncSession = Depends(get_session),
) -> AuthGuard:
    """
    Route dependency that verifies the decoded token's user and session.
    """
    print("token_data", token_data)
    user_id = token_data.user_id
    session_id = token_data.session_id

    # Validate user
    user = await db.scalar(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Validate session
    session = await db.scalar(
        select(Session).where(
            Session.id == session_id, Session.user_id == user_id, Session.valid == True
        )
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    print("Herro")
    return AuthGuard(user_id=user_id, session_id=session_id)
