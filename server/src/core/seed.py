import asyncio
import json
import pandas as pd
from sqlmodel import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.api.models import (
    Genre,
    Actor,
    Director,
    Movie,
    Year,
)
from src.core import init_db
from .database import engine

BASE_PATH = "src/data/datasets"


def load_data(filename: str) -> pd.DataFrame:
    path = f"{BASE_PATH}/{filename}"
    if path.endswith(".csv"):
        return pd.read_csv(path)
    elif path.endswith(".json"):
        with open(path, "r") as f:
            data = json.load(f)
            # Convert dict → DataFrame
        df = pd.DataFrame(list(data.items()), columns=["genre", "image_url"])
        print(df.head(1))
        return df
    else:
        raise ValueError(f"Unsupported file type: {filename}")


async def seed_genres(session: AsyncSession):
    df = load_data("genre_image_urls.json")
    print("Seeding Genres...")
    for _, row in df.iterrows():
        exists = await session.scalar(select(Genre).where(Genre.genre == row["genre"]))
        if not exists:
            genre = Genre(genre=row["genre"], image_url=row.get("image_url"))
            session.add(genre)
    await session.commit()
    print("Genres seeded.")


async def seed_actors(
    session: AsyncSession, df_movies: pd.DataFrame, df_actor_images: pd.DataFrame
):
    print("Seeding Actors...")
    # Build a mapping of actor name → image_url
    actor_images = df_actor_images.set_index("actor")["image_url"].to_dict()

    # Extract all unique actors from clean_data.csv
    unique_actors = set()
    for a_list in df_movies["actors"].dropna():
        unique_actors.update([a.strip() for a in a_list.split("|")])

    for name in unique_actors:
        exists = await session.scalar(select(Actor).where(Actor.name == name))
        if not exists:
            actor = Actor(name=name, image_url=actor_images.get(name))
            session.add(actor)
    await session.commit()
    print("Actors seeded.")


async def seed_directors(
    session: AsyncSession, df_movies: pd.DataFrame, df_director_images: pd.DataFrame
):
    print("Seeding Directors...")
    director_images = df_director_images.set_index("director")["image_url"].to_dict()

    unique_directors = set()
    for d_list in df_movies["directors"].dropna():
        unique_directors.update([d.strip() for d in d_list.split("|")])

    for name in unique_directors:
        exists = await session.scalar(select(Director).where(Director.name == name))
        if not exists:
            director = Director(name=name, image_url=director_images.get(name))
            session.add(director)
    await session.commit()
    print("Directors seeded.")


async def seed_years(session: AsyncSession):
    df_years = load_data("movie_year.csv")
    print("Seeding Years...")

    unique_years = df_years["year"].unique()
    for y in unique_years:
        exists = await session.scalar(select(Year).where(Year.year == int(y)))
        if not exists:
            year = Year(year=int(y))
            session.add(year)
    await session.commit()
    print("Years seeded.")


async def seed_movies(session: AsyncSession):
    df_movies = load_data("clean_data.csv")
    df_actor_images = load_data("actor_summary.csv")
    df_director_images = load_data("director_summary.csv")
    df_years = load_data("movie_year.csv")

    await seed_actors(session, df_movies, df_actor_images)
    await seed_directors(session, df_movies, df_director_images)

    print("Seeding Movies...")
    # Load genres from DB
    genre_map = {g.genre: g for g in (await session.execute(select(Genre))).scalars()}
    # Load actors/directors from DB
    actor_map = {a.name: a for a in (await session.execute(select(Actor))).scalars()}
    director_map = {
        d.name: d for d in (await session.execute(select(Director))).scalars()
    }
    year_map = {y.year: y for y in (await session.execute(select(Year))).scalars()}

    df_movies = df_movies.merge(df_years, on="movieId", how="left")

    for _, row in df_movies.iterrows():
        exists = await session.scalar(
            select(Movie).where(Movie.tmdb_id == row["tmdbId"])
        )
        if exists:
            continue

        year_obj = year_map.get(int(row["year"]))
        if not year_obj:
            continue

        movie_data = {
            "id": row["movieId"],
            "original_title": row["original_title"],
            "overview": row["overview"],
            "original_language": row["original_language"],
            "poster_path": row["poster_path"],
            "avg_rating": row["avg_rating"],
            "total_rating_users": row["total_rating_users"],
            "popularity_score": row["popularity_score"],
            "tmdb_id": row["tmdbId"],
            "year_id": year_obj.id,
        }
        movie = Movie(**movie_data)

        # Link genres
        for g_name in row["genres"].split("|"):
            genre = genre_map.get(g_name.strip())
            if genre:
                movie.genres.append(genre)

        # Link actors
        for a_name in row["actors"].split("|"):
            actor = actor_map.get(a_name.strip())
            if actor:
                movie.actors.append(actor)

        # Link directors
        for d_name in row["directors"].split("|"):
            director = director_map.get(d_name.strip())
            if director:
                movie.directors.append(director)

        session.add(movie)
        await session.flush()  # So movie.id is available for relationships

    await session.commit()
    print("Movies seeded.")


async def seed_db():
    await init_db()

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        await seed_genres(session)
        await seed_years(session)
        await seed_movies(session)


async def create_fts_table(session: AsyncSession):
    # Create virtual FTS5 table for movie title search
    await session.execute(
        text(
            """
        CREATE VIRTUAL TABLE IF NOT EXISTS movie_title_fts
        USING fts5(
            movie_id UNINDEXED,
            title,
            tokenize='unicode61'
        );
    """
        )
    )

    # Populate table from Movie
    await session.execute(text("DELETE FROM movie_title_fts;"))
    await session.execute(
        text(
            """
        INSERT INTO movie_title_fts(movie_id, title)
        SELECT id, original_title FROM movie;
    """
        )
    )
    await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_db())
    print("Database seeded.")
