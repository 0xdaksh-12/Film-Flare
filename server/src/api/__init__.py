from .routes import auth_router, user_router, movie_router

from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(movie_router, prefix="/movies", tags=["Movies"])
