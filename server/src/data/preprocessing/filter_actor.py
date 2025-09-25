import time
import requests
import pandas as pd

TMDB_API_KEY = "549d74d021bd35eac9d680ec3ec9aacf"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def fetch_director_image(name: str, max_retries: int = 3) -> str | None:
    """Fetch director profile image from TMDB API with retry on rate limits."""
    url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={name}"

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=10)

            # Handle rate limit (HTTP 429)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 10))
                print(
                    f"⏳ Rate limited while fetching {name}. Sleeping for {retry_after}s..."
                )
                time.sleep(retry_after)
                continue  # retry again

            resp.raise_for_status()
            data = resp.json()

            if data.get("results"):
                profile_path = data["results"][0].get("profile_path")
                if profile_path:
                    return f"{TMDB_IMAGE_BASE}{profile_path}"
            return None

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching {name} (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
            else:
                return None
    return None


df = pd.read_csv("./data/clean_data.csv")

print(df.isnull().sum())

actors_df = (
    df.assign(actor=df["actors"].str.split("|"))
    .explode("actor")
    .drop(columns=["actors"])
)

actor_summary = (
    actors_df.groupby("actor", as_index=False)
    .agg(
        movies_count=("movieId", "count"),
        total_users=("total_rating_users", "sum"),
        avg_rating=("avg_rating", "mean"),
    )
    .sort_values(by="movies_count", ascending=False)
)

# print(actor_summary.head(10))
# actor_summary[actor_summary.actor == 'Jackie Chan']
actor_summary_filtered = actor_summary[
    (actor_summary["total_users"] > 20) & (actor_summary["movies_count"] > 5)
].reset_index()

print(actor_summary_filtered)

actor_summary_filtered["image_url"] = actor_summary_filtered["actor"].apply(
    fetch_director_image
)


actor_summary_filtered.to_csv("./data/actor_summary.csv", index=False)

print("actor_summary.csv saved successfully with image URLs!")

print(actor_summary_filtered[actor_summary_filtered.actor == "Jackie Chan"])
