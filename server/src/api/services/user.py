from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from uuid import UUID

from src.core import get_session
from src.api.models import User
import src.api.schemas as UserSchema
from src.api.models import UserRating


class UserService:
    """Handles user-related opeartions"""

    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session: AsyncSession = session

    async def get_me(self, user_id: UUID) -> UserSchema.UserMe:
        try:
            user = await self.session.scalar(select(User).where(User.id == user_id))

            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            return UserSchema.UserMe(
                name=user.name,
                profilePic=user.profile_pic if user.profile_pic else None,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user",
            )

        finally:
            await self.session.close()
