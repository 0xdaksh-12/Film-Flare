import pandas as pd
import requests
import time
import math
from typing import Dict, Any

# TMDB API settings
TMDB_API_KEY = ""  # Replace with your actual key
TMDB_BASE_URL = "https://api.themoviedb.org/3/movie/"
TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"  # For poster paths


def fetch_tmdb_details(tmdb_id: int) -> Dict[str, Any]:
    """
    Fetch movie details from TMDB API.
    Returns a dict with title, overview, original_language, poster_path, actors (top 5), directors.
    """
    url = f"{TMDB_BASE_URL}{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract fields
        title = data.get("title", "N/A")
        overview = data.get("overview", "N/A")
        original_language = data.get("original_language", "N/A")
        poster_path = (
            f"{TMDB_POSTER_BASE_URL}{data.get('poster_path')}"
            if data.get("poster_path")
            else "N/A"
        )

        # Actors: Top 5 by popularity/order
        actors = [cast["name"] for cast in data.get("credits", {}).get("cast", [])[:5]]
        actors_str = "|".join(actors) if actors else "N/A"

        # Directors: From crew
        directors = [
            crew["name"]
            for crew in data.get("credits", {}).get("crew", [])
            if crew["job"] == "Director"
        ]
        directors_str = "|".join(directors) if directors else "N/A"

        return {
            "original_title": title,
            "overview": overview,
            "original_language": original_language,
            "poster_path": poster_path,
            "actors": actors_str,
            "directors": directors_str,
        }
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching TMDB ID {tmdb_id}: {e}")
        return {
            "original_title": "N/A",
            "overview": "N/A",
            "original_language": "N/A",
            "poster_path": "N/A",
            "actors": "N/A",
            "directors": "N/A",
        }


# Step 1: Load datasets
print("Loading MovieLens datasets...")
links_df = pd.read_csv("./data/links.csv")
movies_df = pd.read_csv("./data/movies.csv")
ratings_df = pd.read_csv("./data/ratings.csv")
print(
    f"Loaded {len(movies_df)} movies, {len(links_df)} links, {len(ratings_df)} ratings."
)

# Step 2: Compute rating stats
print("Computing average ratings and total rating users...")
rating_stats = (
    ratings_df.groupby("movieId")
    .agg(avg_rating=("rating", "mean"), total_rating_users=("userId", "nunique"))
    .reset_index()
)

# Step 3: Merge datasets
print("Merging datasets...")
merged_df = links_df.merge(movies_df, on="movieId", how="left").merge(
    rating_stats, on="movieId", how="left"
)
print(f"Merged dataset shape: {merged_df.shape}")

# Step 4: Fill NaNs and compute popularity
print("Filling missing values and computing popularity score...")
merged_df["avg_rating"] = merged_df["avg_rating"].fillna(0)
merged_df["total_rating_users"] = merged_df["total_rating_users"].fillna(0)
merged_df["popularity_score"] = merged_df["avg_rating"] * merged_df[
    "total_rating_users"
].apply(lambda x: math.log(x + 1))

# Step 5: Fetch TMDB details
print("🎬 Fetching TMDB details (this may take a while)...")
tmdb_details = []
progress_interval = 50  # print progress every N movies

for idx, row in merged_df.iterrows():
    tmdb_id = row["tmdbId"]
    if pd.notna(tmdb_id):
        details = fetch_tmdb_details(int(tmdb_id))
        tmdb_details.append(details)
    else:
        tmdb_details.append(
            {
                "original_title": "N/A",
                "overview": "N/A",
                "original_language": "N/A",
                "poster_path": "N/A",
                "actors": "N/A",
                "directors": "N/A",
            }
        )

    # Progress log
    # if (idx + 1) % progress_interval == 0:
    #     print(f"Processed {int(idx) + 1}/{len(merged_df)} movies...")

    time.sleep(0.25)  # Rate limit: ~4 requests/sec

print("Finished fetching TMDB details.")

# Step 6: Merge enriched data
print("Combining TMDB details with base dataset...")
tmdb_df = pd.DataFrame(tmdb_details)
enriched_df = pd.concat([merged_df, tmdb_df], axis=1)

# Step 7: Reorder and save
print("Saving enriched dataset to 'enriched_movies.csv'...")
columns_order = [
    "movieId",
    "original_title",
    "genres",
    "actors",
    "directors",
    "overview",
    "original_language",
    "poster_path",
    "avg_rating",
    "total_rating_users",
    "popularity_score",
    "imdbId",
    "tmdbId",
]
enriched_df = enriched_df[columns_order]

enriched_df.to_csv("enriched_movies.csv", index=False)
print("Enriched dataset saved successfully to 'enriched_movies.csv'.")
