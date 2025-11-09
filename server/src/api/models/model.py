from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from src.api.utils import now_utc
from src.api.schemas import AuthProvider


class User(SQLModel, table=True):
    __tablename__: str = "user"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True)
    profile_pic: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    email_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    auth: Optional["UserAuth"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"uselist": False}
    )
    sessions: list["Session"] = Relationship(back_populates="user")
    ratings: list["UserRating"] = Relationship(back_populates="user")


class UserAuth(SQLModel, table=True):
    __tablename__: str = "user_auth"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    provider: AuthProvider = Field(index=True)

    email: EmailStr = Field(index=True, unique=True)
    password_hash: Optional[str] = Field(default=None, repr=False)

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    user: User = Relationship(back_populates="auth")


class Session(SQLModel, table=True):
    __tablename__: str = "session"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)

    user_agent: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    refresh_token_hash: Optional[str] = Field(default=None, repr=False)
    valid: bool = Field(default=True)

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    user: User = Relationship(back_populates="sessions")


class MovieData(SQLModel, table=True):
    __tablename__: str = "movie_data"

    movie_id: int = Field(
        foreign_key="movie.id", index=True, unique=True, primary_key=True
    )

    # Flattened fields
    title: str
    genres: str
    directors: str
    actors: str
    overview: str


class MovieGenreLink(SQLModel, table=True):
    __tablename__: str = "movie_genre_link"

    movie_id: int = Field(foreign_key="movie.id", primary_key=True)
    genre_id: UUID = Field(foreign_key="genre.id", primary_key=True)


class MovieActorLink(SQLModel, table=True):
    __tablename__: str = "movie_actor_link"

    movie_id: int = Field(foreign_key="movie.id", primary_key=True)
    actor_id: UUID = Field(foreign_key="actor.id", primary_key=True)


class MovieDirectorLink(SQLModel, table=True):
    __tablename__: str = "movie_director_link"

    movie_id: int = Field(foreign_key="movie.id", primary_key=True)
    director_id: UUID = Field(foreign_key="director.id", primary_key=True)


class Genre(SQLModel, table=True):
    __tablename__: str = "genre"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    genre: str = Field(index=True)
    image_url: Optional[str] = Field(default=None)

    movies: list["Movie"] = Relationship(
        back_populates="genres", link_model=MovieGenreLink
    )


class Actor(SQLModel, table=True):
    __tablename__: str = "actor"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True)
    image_url: Optional[str] = Field(default=None)

    movies: list["Movie"] = Relationship(
        back_populates="actors", link_model=MovieActorLink
    )


class Director(SQLModel, table=True):
    __tablename__: str = "director"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True)
    image_url: Optional[str] = Field(default=None)

    movies: list["Movie"] = Relationship(
        back_populates="directors", link_model=MovieDirectorLink
    )


class Year(SQLModel, table=True):
    __tablename__: str = "year"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    year: int = Field(index=True, unique=True)

    movies: list["Movie"] = Relationship(back_populates="year")


class Movie(SQLModel, table=True):
    __tablename__: str = "movie"

    id: int = Field(primary_key=True, index=True)
    original_title: str = Field(index=True)
    overview: str
    original_language: str = Field(index=True)
    poster_path: str
    avg_rating: float
    total_rating_users: int
    popularity_score: float = Field(index=True)
    tmdb_id: int = Field(index=True)
    year_id: UUID = Field(foreign_key="year.id", index=True)

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    genres: list[Genre] = Relationship(
        back_populates="movies", link_model=MovieGenreLink
    )
    actors: list[Actor] = Relationship(
        back_populates="movies", link_model=MovieActorLink
    )
    directors: list[Director] = Relationship(
        back_populates="movies", link_model=MovieDirectorLink
    )
    ratings: list["UserRating"] = Relationship(back_populates="movie")
    year: Year = Relationship(back_populates="movies")


class UserRating(SQLModel, table=True):
    __tablename__: str = "user_rating"
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    movie_id: int = Field(foreign_key="movie.id", primary_key=True)
    rating: int = Field(ge=1, le=5)

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    user: User = Relationship(back_populates="ratings")
    movie: Movie = Relationship(back_populates="ratings")
