import pickle
import aiofiles
from typing import List, Dict, Any, Tuple

_cache: Dict[str, Any] = {
    "movie_dict": None,
    "similarity": None,
    "movie_id_to_index": None,
    "index_to_movie_id": None,
}

MOVIE_DICT_PATH = "src/data/ml/models/movie_dict.pkl"
SIMILARITY_PATH = "src/data/ml/models/similarity.pkl"


async def _load_models_if_needed() -> None:
    """Load pickles into memory once, cache them globally."""
    if _cache["movie_dict"] is not None and _cache["similarity"] is not None:
        return  # Already loaded

    async with aiofiles.open(MOVIE_DICT_PATH, "rb") as f:
        movie_dict_bytes = await f.read()
    async with aiofiles.open(SIMILARITY_PATH, "rb") as f:
        similarity_bytes = await f.read()

    movie_dict = pickle.loads(movie_dict_bytes)
    similarity = pickle.loads(similarity_bytes)

    # Extract and store mappings
    index_to_movie_id = movie_dict["movie_id"]
    movie_id_to_index = {v: k for k, v in index_to_movie_id.items()}

    _cache.update(
        {
            "movie_dict": movie_dict,
            "similarity": similarity,
            "index_to_movie_id": index_to_movie_id,
            "movie_id_to_index": movie_id_to_index,
        }
    )


async def similar(movieId: int) -> List[int]:
    """
    Return top 10 similar movie IDs for the given movieId.
    Uses cached data (loads only once on first call).
    """
    await _load_models_if_needed()

    movie_id_to_index = _cache["movie_id_to_index"]
    index_to_movie_id = _cache["index_to_movie_id"]
    similarity = _cache["similarity"]

    # Validate movieId
    if movieId not in movie_id_to_index:
        return []

    movie_index = movie_id_to_index[movieId]
    if movie_index >= len(similarity):
        return []

    distances = similarity[movie_index]

    # Sort and exclude itself
    top_indices = [
        i
        for i, _ in sorted(enumerate(distances), key=lambda x: x[1], reverse=True)
        if i != movie_index
    ][:10]

    # Convert indices back to movie IDs
    top_movie_ids = [
        index_to_movie_id[i] for i in top_indices if i in index_to_movie_id
    ]

    return top_movie_ids


async def recommend_for_new_user(
    user_ratings: List[Tuple[int, float]], min_rating: float = 4.0, top_n: int = 10
) -> List[int]:
    """
    Recommend movies for a new user based on movies they rated highly (>= min_rating).

    Args:
        user_ratings: list of (movie_id, rating)
        min_rating: minimum rating to consider
        top_n: number of recommendations to return

    Returns:
        List of top recommended movie IDs.
    """
    await _load_models_if_needed()

    movie_id_to_index = _cache["movie_id_to_index"]
    index_to_movie_id = _cache["index_to_movie_id"]
    similarity = _cache["similarity"]

    # Filter liked movies
    liked_movies = [mid for mid, r in user_ratings if r >= min_rating]
    if not liked_movies:
        return []

    candidate_scores: Dict[int, float] = {}

    for mid in liked_movies:
        if mid not in movie_id_to_index:
            continue
        movie_idx = movie_id_to_index[mid]
        distances = similarity[movie_idx]

        # Get top similar movies (excluding itself)
        top_indices = [
            i
            for i, _ in sorted(enumerate(distances), key=lambda x: x[1], reverse=True)
            if i != movie_idx
        ][
            :50
        ]  # use more neighbors for better aggregation

        for idx in top_indices:
            other_id = index_to_movie_id.get(idx)
            if not other_id or other_id in liked_movies:
                continue
            candidate_scores[other_id] = candidate_scores.get(other_id, 0.0) + float(
                distances[idx]
            )

    if not candidate_scores:
        return []

    # Sort aggregated scores
    ranked = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
    recommended_ids = [mid for mid, _ in ranked[:top_n]]
    return recommended_ids
