from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, col, func, case, text
from sqlalchemy.orm import selectinload, InstrumentedAttribute
from typing import cast
from uuid import UUID

from src.data.ml import similar, recommend_for_new_user
from src.core import get_session
from src.api.models import (
    Movie,
    Genre,
    Year,
    MovieGenreLink,
    MovieData,
    UserRating,
)
import src.api.schemas as MovieSchema
from src.api.utils import now_utc


class MovieService:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self.session = session

    async def search(self, q: str, limit: int, offset: int) -> list[MovieSchema.Movie]:
        # Perform FTS search with ranking
        stmt = text(
            """
            SELECT m.id, m.original_title, m.overview, m.poster_path, m.avg_rating
            FROM movie_title_fts
            JOIN movie m ON m.id = movie_title_fts.movie_id
            JOIN year y ON y.id = m.year_id
            WHERE movie_title_fts MATCH :query
            ORDER BY y.year DESC, m.total_rating_users DESC
            LIMIT :limit OFFSET :offset;
            """
        )

        result = await self.session.execute(
            stmt, {"query": q, "limit": limit, "offset": offset}
        )
        rows = result.fetchall()

        movies_out = [
            MovieSchema.Movie(
                id=row.id,
                original_title=row.original_title,
                overview=row.overview,
                poster_path=row.poster_path,
                avg_rating=row.avg_rating,
            )
            for row in rows
        ]

        return movies_out

    async def top_trending(self) -> list[MovieSchema.MovieTrending] | None:
        stmt = (
            select(Movie)
            .options(
                selectinload(cast(InstrumentedAttribute, Movie.genres)),
                selectinload(cast(InstrumentedAttribute, Movie.actors)),
                selectinload(cast(InstrumentedAttribute, Movie.directors)),
                selectinload(cast(InstrumentedAttribute, Movie.year)),
            )
            .join(Year, col(Movie.year_id) == col(Year.id))
            .where(col(Year.year) > 2017)
            .order_by(
                col(Movie.popularity_score).desc(),
                col(Movie.avg_rating).desc(),
            )
            .limit(8)
        )

        result = await self.session.execute(stmt)
        movies = result.scalars().unique().all()

        movies_out = []

        for m in movies:
            # Preload related data efficiently (already attached if relationships are configured)
            genres = [g.genre for g in m.genres] if m.genres else []
            actors = [a.name for a in m.actors] if m.actors else []
            directors = [d.name for d in m.directors] if m.directors else []

            movies_out.append(
                MovieSchema.MovieTrending(
                    id=m.id,
                    original_title=m.original_title,
                    overview=m.overview,
                    poster_path=m.poster_path,
                    avg_rating=m.avg_rating,
                    genres=genres,
                    year=m.year.year,
                )
            )

        return movies_out if movies_out else None

    async def get_genres(self) -> list[str] | None:
        stmt = select(Genre)
        result = await self.session.execute(stmt)
        genres = result.scalars().all()
        if genres:
            return [g.genre for g in genres]

        return None

    async def top_rating(
        self, q: str | None, limit: int = 10, offset: int = 0
    ) -> list[MovieSchema.Movie] | None:
        stmt = (
            select(Movie)
            .join(Year)
            .options(selectinload(cast(InstrumentedAttribute, Movie.year)))
            .where(col(Movie.total_rating_users) >= 30)
            .order_by(
                col(Year.year).desc(),
                col(Movie.avg_rating).desc(),
                col(Movie.total_rating_users).desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        if q:
            genres = [g.strip() for g in q.replace("|", ",").split(",") if g.strip()]
            stmt = (
                stmt.join(MovieGenreLink)
                .join(Genre)
                .where(col(Genre.genre).in_(genres))
                .where(col(Movie.total_rating_users) >= 30)
                .order_by(
                    col(Year.year).desc(),
                    col(Movie.avg_rating).desc(),
                    col(Movie.total_rating_users).desc(),
                )
                .limit(limit)
                .offset(offset)
            )

        result = await self.session.execute(stmt)
        movies = result.scalars().unique().all()

        movies_out = [
            MovieSchema.Movie(
                id=m.id,
                original_title=m.original_title,
                overview=m.overview,
                poster_path=m.poster_path,
                avg_rating=m.avg_rating,
            )
            for m in movies
        ]

        return movies_out

    async def get_movie(
        self, movieId: int, user_id: UUID | None = None
    ) -> MovieSchema.MovieDetail | None:
        stmt = (
            select(Movie)
            .where(Movie.id == movieId)
            .options(
                selectinload(cast(InstrumentedAttribute, Movie.genres)),
                selectinload(cast(InstrumentedAttribute, Movie.actors)),
                selectinload(cast(InstrumentedAttribute, Movie.directors)),
                selectinload(cast(InstrumentedAttribute, Movie.year)),
            )
        )

        result = await self.session.execute(stmt)
        movie = result.scalar_one_or_none()

        if not movie:
            return None

        user_rating_value: int | None = None
        if user_id:
            rating_stmt = select(UserRating).where(
                UserRating.user_id == user_id, UserRating.movie_id == movieId
            )
            rating_result = await self.session.execute(rating_stmt)
            user_rating = rating_result.scalar_one_or_none()
            if user_rating:
                user_rating_value = user_rating.rating

        return MovieSchema.MovieDetail(
            id=movie.id,
            original_title=movie.original_title,
            overview=movie.overview,
            poster_path=movie.poster_path,
            avg_rating=movie.avg_rating,
            genres=[g.genre for g in movie.genres],
            actors=[a.name for a in movie.actors],
            directors=[d.name for d in movie.directors],
            year=movie.year.year,
            user_rating=user_rating_value,
        )

    async def get_similar_movies(self, movieId: int) -> list[MovieSchema.Movie] | None:
        # Check if movieId exist
        stmt = (
            select(Movie)
            .where(Movie.id == movieId)
            .options(
                selectinload(cast(InstrumentedAttribute, Movie.genres)),
                selectinload(cast(InstrumentedAttribute, Movie.actors)),
                selectinload(cast(InstrumentedAttribute, Movie.directors)),
            )
        )

        result = await self.session.execute(stmt)
        movie = result.scalar_one_or_none()

        if not movie:
            return None

        # List of Movie id that are similar
        similar_movie_ids: list[int] = await similar(movie.id)

        if not similar_movie_ids:
            return []

        print(f"\033[31m{similar_movie_ids}\033[0m")

        # Fetch all similar movies
        stmt_similar = (
            select(Movie)
            .where(col(Movie.id).in_(similar_movie_ids))
            .options(
                selectinload(cast(InstrumentedAttribute, Movie.genres)),
                selectinload(cast(InstrumentedAttribute, Movie.actors)),
                selectinload(cast(InstrumentedAttribute, Movie.directors)),
            )
        )
        result_similar = await self.session.execute(stmt_similar)
        similar_movies = result_similar.scalars().all()

        # Preserve similarity order (since IN() does not guarantee order)
        id_to_movie = {m.id: m for m in similar_movies}
        ordered_movies = [
            id_to_movie[mid] for mid in similar_movie_ids if mid in id_to_movie
        ]

        # Convert to schema objects
        movies_out = [
            MovieSchema.Movie(
                id=m.id,
                original_title=m.original_title,
                overview=m.overview,
                poster_path=m.poster_path,
                avg_rating=m.avg_rating,
            )
            for m in ordered_movies
        ]

        return movies_out

    async def build_movie_data(self):
        stmt = select(Movie).options(
            selectinload(cast(InstrumentedAttribute, Movie.genres)),
            selectinload(cast(InstrumentedAttribute, Movie.actors)),
            selectinload(cast(InstrumentedAttribute, Movie.directors)),
        )

        result = await self.session.execute(stmt)
        movies = result.scalars().unique().all()

        for movie in movies:
            genres = "|".join([g.genre for g in movie.genres])
            directors = "|".join([d.name for d in movie.directors])
            actors = "|".join([a.name for a in movie.actors])

            data = MovieData(
                movie_id=movie.id,
                title=movie.original_title,
                genres=genres,
                directors=directors,
                actors=actors,
                overview=movie.overview,
            )
            self.session.add(data)

        await self.session.commit()

    async def rate_movie(self, movie_id: int, user_id: UUID, rating: int):
        print(f"\033[31m Start HERE\033[0m")
        movie_stmt = select(Movie).where(Movie.id == movie_id)
        movie_result = await self.session.execute(movie_stmt)
        movie = movie_result.scalar_one_or_none()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        stmt = select(UserRating).where(
            UserRating.user_id == user_id, UserRating.movie_id == movie_id
        )
        result = await self.session.execute(stmt)
        existing_rating = result.scalar_one_or_none()

        print(f"\033[31m{existing_rating} existing_rating\033[0m")
        if existing_rating:
            # Update user's previous rating
            existing_rating.rating = rating
            existing_rating.updated_at = now_utc()
            print(f"\033[31m{existing_rating} PREVIOUS existing_rating\033[0m")
        else:
            # Add new rating
            new_rating = UserRating(user_id=user_id, movie_id=movie_id, rating=rating)
            self.session.add(new_rating)
            print(f"\033[31m{existing_rating} NEW existing_rating\033[0m")

        print(f"\033[31m{existing_rating} UPDATE\033[0m")
        # Update movie stats incrementally
        if existing_rating:
            print(f"\033[31m{existing_rating} FUCK HOW \033[0m")
            # If user updated their rating, recalc avg by subtracting old, adding new
            total = movie.total_rating_users
            movie.avg_rating = (
                (movie.avg_rating * total) - existing_rating.rating + rating
            ) / total
            print(f"\033[31m{total} {movie} FUCK HOW \033[0m")
        else:
            # New user rating, add to total
            total = movie.total_rating_users + 1
            movie.avg_rating = (
                (movie.avg_rating * movie.total_rating_users) + rating
            ) / total
            movie.total_rating_users = total
            print(f"\033[31m{total} {movie} FUCK HOW \033[0m")

        movie.updated_at = now_utc()
        await self.session.commit()

        return {"success": True}

    async def get_high_rated_movies(
        self, user_id: UUID, min_rating: int = 4
    ) -> list[int]:
        """Return list of movie IDs rated >= min_rating."""
        try:
            stmt = select(UserRating.movie_id).where(
                (UserRating.user_id == user_id) & (UserRating.rating >= min_rating)
            )
            result = await self.session.execute(stmt)
            return [row[0] for row in result.all()]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch rated movies: {e}",
            )

    async def get_personalized_recommendations(
        self, user_id: UUID, min_rating: int = 4, top_n: int = 10
    ) -> MovieSchema.RecommendationResponse:
        """
        Returns personalized 'You Might Like' recommendations for a user.
        Unlocks after user rated >=5 movies with rating >= min_rating.
        """
        high_rated_movies = await self.get_high_rated_movies(user_id, min_rating)

        # Case 1: Not enough movies rated yet
        if len(high_rated_movies) < 5:
            return MovieSchema.RecommendationResponse(
                unlocked=False, count=len(high_rated_movies)
            )

        # Simulate ratings (we only care about liked movies)
        user_ratings = [(mid, 4.0) for mid in high_rated_movies]

        # Get recommended movie IDs from ML model
        rec_ids = await recommend_for_new_user(
            user_ratings, min_rating=min_rating, top_n=top_n
        )

        # Case 2: Unlock but no recommendations found
        if not rec_ids:
            return MovieSchema.RecommendationResponse(unlocked=True, recommendations=[])

        # Fetch movies from DB
        stmt = (
            select(Movie)
            .where(col(Movie.id).in_(rec_ids))
            .options(
                selectinload(cast(InstrumentedAttribute, Movie.genres)),
                selectinload(cast(InstrumentedAttribute, Movie.actors)),
                selectinload(cast(InstrumentedAttribute, Movie.directors)),
            )
        )
        result = await self.session.execute(stmt)
        movies = result.scalars().all()

        # Preserve rec_ids order
        id_to_movie = {m.id: m for m in movies}
        ordered_movies = [id_to_movie[mid] for mid in rec_ids if mid in id_to_movie]

        recommendations: list[MovieSchema.Movie] = [
            MovieSchema.Movie(
                id=m.id,
                original_title=m.original_title,
                overview=m.overview,
                poster_path=m.poster_path,
                avg_rating=m.avg_rating,
            )
            for m in ordered_movies
        ]

        return MovieSchema.RecommendationResponse(
            unlocked=True, recommendations=recommendations
        )
