from pydantic import BaseModel, Field
from typing import Optional


"""
Schemas for Movie API

This module contains the pydantic models for the Movie API.

The Movie model contains the basic information about a movie, such as its ID, original title, overview, poster path, average rating, and total number of users who have rated the movie.

The MovieDetail model extends the Movie model and adds fields for the genres, actors, and directors of the movie.

"""


class Movie(BaseModel):
    """Basic information about a movie.

    Attributes:
        id (int): The ID of the movie.
        original_title (str): The original title of the movie.
        overview (str): The overview of the movie.
        poster_path (str): The URL of the poster of the movie.
        avg_rating (float): The average rating of the movie.
        total_rating_users (int): The total number of users who have rated the movie.
    """

    id: int
    original_title: str
    overview: str
    poster_path: str
    avg_rating: float


class MovieTrending(Movie):
    genres: list[str]
    year: int


class MovieDetail(Movie):
    """Detailed information about a movie.

    Attributes:
        genres (list[str]): The genres of the movie.
        actors (list[str]): The actors of the movie.
        directors (list[str]): The directors of the movie.
    """

    genres: list[str]
    actors: list[str]
    directors: list[str]
    year: int
    user_rating: int | None


class MovieRatingIn(BaseModel):
    rating: int = Field(ge=1, le=5)


class RecommendationResponse(BaseModel):
    unlocked: bool
    count: Optional[int] = None
    recommendations: Optional[list[Movie]] = None
