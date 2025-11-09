from fastapi import APIRouter, status, Depends
import src.api.schemas as schema
from src.api.services import UserService
from src.api.dependencies import auth_guard


user_router = APIRouter()


@user_router.get("/me", response_model=schema.UserMe, status_code=status.HTTP_200_OK)
async def getMe(
    auth_data: schema.AuthGuard = Depends(auth_guard),
    user_service: UserService = Depends(),
) -> schema.UserMe:
    return await user_service.get_me(auth_data.user_id)
