import re
import pandas as pd


movies_df = pd.read_csv("./data/movies.csv")
enriched_df = pd.read_csv("./data/enriched_movies.csv")


def get_decade(title: str) -> str:
    """
    Extract release year from title (e.g., 'Movie (1995)') and compute decade shorthand.
    - 1990-1999: '90s'
    - 1980-1989: '80s'
    - 2000-2009: '2000s'
    - 2010-2019: '2010s'
    - etc.
    Returns 'N/A' if no valid year found.
    """
    year_match = re.search(r"\((\d{4})\)", title)
    if year_match:
        year = int(year_match.group(1))
        decade = (year // 10) * 10
        if decade >= 2000:
            return f"{decade}s"
        else:
            return f"{str(decade % 100)}s"  # 1990 -> '90s', 1980 -> '80s'
    return "N/A"


enriched_df["decade"] = movies_df["title"].apply(get_decade)

enriched_df.dropna(inplace=True)
enriched_df.drop(columns=["imdbId"], inplace=True)
print(enriched_df.isnull().sum())

enriched_df.to_csv("./data/clean_data.csv", index=False)

df = pd.read_csv("./data/clean_data.csv")


df["genres"] = (
    df["genres"].str.replace(r"\|?IMAX\|?", "", regex=True).str.strip("|")
)  # Remove IMAX and extra pipes
df["genres"] = df["genres"].replace(
    "", "(no genres listed)"
)  # Handle any now-empty genres
df["avg_rating"] = round(df["avg_rating"], 2)
df["total_rating_users"] = df["total_rating_users"].astype(int)
df["tmdbId"] = df["tmdbId"].astype(int)
df = df[df.genres != "(no genres listed)"]

print(df.isnull().sum())
df.dropna(inplace=True)

df.to_csv("./data/clean_data.csv", index=False)

df = pd.read_csv("./data/clean_data.csv")

print(df.isnull().sum())
