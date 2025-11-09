from fastapi import APIRouter, status, Depends, Query
from src.api.dependencies import auth_guard
import src.api.schemas as schema
from src.api.services import MovieService
from src.api.dependencies import auth_guard
from uuid import UUID


movie_router = APIRouter()


@movie_router.get(
    "/search", response_model=list[schema.Movie], status_code=status.HTTP_200_OK
)
async def search_movie(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Number of movies to fetch"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    movie_service: MovieService = Depends(),
) -> list[schema.Movie]:
    return await movie_service.search(q, limit, offset)


@movie_router.get(
    "/trending",
    response_model=list[schema.MovieTrending],
    status_code=status.HTTP_200_OK,
)
async def trending_movie(
    movie_service: MovieService = Depends(),
) -> list[schema.MovieTrending] | None:
    return await movie_service.top_trending()


@movie_router.get("/genres", response_model=list[str], status_code=status.HTTP_200_OK)
async def genres(movie_service: MovieService = Depends()) -> list[str] | None:
    return await movie_service.get_genres()


@movie_router.get(
    "/top_rated", response_model=list[schema.Movie], status_code=status.HTTP_200_OK
)
async def top_rated(
    q: str | None = Query(None, description="For Genres Based Rating"),
    limit: int = Query(10, ge=1, le=50, description="Number of movies to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    movie_service: MovieService = Depends(),
) -> list[schema.Movie] | None:
    return await movie_service.top_rating(q=q, limit=limit, offset=offset)


@movie_router.get(
    "/recommendations",
    response_model=schema.RecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def personalized_recommendations(
    auth_data: schema.AuthGuard = Depends(auth_guard),
    movie_service: MovieService = Depends(),
) -> schema.RecommendationResponse:

    print("KJSDjfljLSJDLJLSJDLJFL")
    return await movie_service.get_personalized_recommendations(auth_data.user_id)


@movie_router.get(
    "/{movieId}", response_model=schema.MovieDetail, status_code=status.HTTP_200_OK
)
async def get_movie(
    movieId: int,
    auth_data: schema.AuthGuard = Depends(auth_guard),
    movie_service: MovieService = Depends(),
) -> schema.MovieDetail | None:
    return await movie_service.get_movie(movieId, auth_data.user_id)


@movie_router.get(
    "/{movieId}/similar",
    response_model=list[schema.Movie],
    status_code=status.HTTP_200_OK,
)
async def similar_movies(
    movieId: int,
    auth_data: schema.AuthGuard = Depends(auth_guard),
    movie_service: MovieService = Depends(),
) -> list[schema.Movie] | None:
    return await movie_service.get_similar_movies(movieId)


@movie_router.post("/admin/build-movie-data")
async def build_movie_data(service: MovieService = Depends()):
    await service.build_movie_data()


@movie_router.post(
    "/{movieId}/rate",
    status_code=status.HTTP_200_OK,
)
async def rate_movie(
    movieId: int,
    payload: schema.MovieRatingIn,
    auth_data: schema.AuthGuard = Depends(auth_guard),
    movie_service: MovieService = Depends(),
):
    data = await movie_service.rate_movie(movieId, auth_data.user_id, payload.rating)
    return data
