import pandas as pd
import requests


TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_API_KEY = "549d74d021bd35eac9d680ec3ec9aacf"


df = pd.read_csv("./data/clean_data.csv")

print(df.isnull().sum())

df_director = df[df["total_rating_users"] >= 30]

director_counts = df_director["directors"].value_counts().reset_index()
director_counts.columns = ["director", "movie_count"]

avg_ratings = df_director.groupby("directors")["avg_rating"].mean().reset_index()
avg_ratings.columns = ["director", "avg_rating"]

summary = pd.merge(director_counts, avg_ratings, on="director")

summary = summary[summary["movie_count"] > 1]
summary = summary.sort_values(by="movie_count", ascending=False).reset_index(drop=True)

print(summary)


def fetch_director_image(name: str) -> str | None:
    """Fetch director profile image from TMDB API."""
    try:
        url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={name}"

        resp = requests.get(url, timeout=10)  # longer timeout
        resp.raise_for_status()
        data = resp.json()

        if data["results"]:
            profile_path = data["results"][0].get("profile_path")
            if profile_path:
                return f"{TMDB_IMAGE_BASE}{profile_path}"
        return None
    except Exception as e:
        print(f"⚠️ Error fetching {name}: {e}")
        return None


summary["image_url"] = summary["director"].apply(fetch_director_image)

summary.to_csv("./data/director_summary.csv", index=False)

print("director_summary.csv saved successfully with image URLs!")
