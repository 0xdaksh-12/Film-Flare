from fastapi import APIRouter, status, Request, Response, Depends, HTTPException
import src.api.schemas as schema
from src.api.services import AuthService
from src.api.dependencies import auth_guard
from src.config import Config


auth_router = APIRouter()


def _extract_client_meta(request: Request) -> schema.ClientMeta:
    """Utility to extract IP and User-Agent headers."""
    return schema.ClientMeta(
        ip_address=getattr(request.client, "host", None),
        user_agent=request.headers.get("User-Agent"),
    )


@auth_router.post(
    "/register", response_model=schema.AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: schema.RegisterRequest,
    fastapi_request: Request,
    response: Response,
    auth_service: AuthService = Depends(),
) -> schema.AuthResponse:
    """Register a new user and set refresh cookie."""
    try:
        client_meta = _extract_client_meta(fastapi_request)
        register_data = schema.RegisterData(
            name=request.name,
            email=request.email,
            password=request.password,
            **client_meta.model_dump(),
        )
        auth_resp = await auth_service.register(register_data, response)
        return schema.AuthResponse(**auth_resp.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {e}",
        )


@auth_router.post(
    "/login", response_model=schema.AuthResponse, status_code=status.HTTP_200_OK
)
async def login(
    request: schema.LoginRequest,
    fastapi_request: Request,
    response: Response,
    auth_service: AuthService = Depends(),
) -> schema.AuthResponse:
    """Authenticate user and set refresh cookie."""
    try:
        client_meta = _extract_client_meta(fastapi_request)
        login_data = schema.LoginData(
            email=request.email,
            password=request.password,
            **client_meta.model_dump(),
        )
        auth_resp = await auth_service.login_user(login_data, response)
        return schema.AuthResponse(**auth_resp.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {e}",
        )


@auth_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
async def logout(
    response: Response,
    auth_data: schema.AuthGuard = Depends(auth_guard),
    auth_service: AuthService = Depends(),
):
    """Invalidate session and clear refresh cookie."""
    try:
        return await auth_service.logout_user(auth_data, response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {e}",
        )


@auth_router.post(
    "/refresh", response_model=schema.AuthResponse, status_code=status.HTTP_200_OK
)
async def refresh(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(),
) -> schema.AuthResponse:
    refresh_token = request.cookies.get(Config.COOKIE_TOKEN)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    try:
        print("Refresh:", refresh_token)
        auth_resp = await auth_service.refresh_token(refresh_token, response)
        return schema.AuthResponse(**auth_resp.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refresh token failed: {e}",
        )
