# FilmFlare

> Backend documentation:
>
> Describes implemented features, API surface, Database Schema, Authentication, Services, ML integration, Recommendation engine (collaborative route), Content-based "similar movies" route, Caching, Startup lifecycle.

## Table of Contents

1. High Level Architecture
2. Runtime & startup lifecycle
3. Configuration & environment
4. Database schema (SQLModel)
5. Authentication & session model
6. API routers & endpoint contracts
7. Service layer (AuthService, UserService, MovieService)
8. Recommendation engine — `/movies/recommendations` (Collaborative)
9. Similar movies — `/movies/{id}/similar` (Content-based)
10. ML integration & model caching
11. Performance, scaling & optimization
12. Security considerations

---

### High-level architecture

- **Backend**: FastAPI using asynchronous execution, SQLModel (SQLAlchemy) for ORM, async DB engine/async sessions.

- **Auth**: JWT-based access tokens + long-lived refresh tokens persisted as HttpOnly cookies. Sessions persisted in DB and bound to a refresh token hash.

- **ML / Recommender**: Hybrid architecture:

  - `/movies/recommendations` presented as a collaborative filtering pipeline that consumes user-item interactions (ratings) and produces recommendations (top-N).

  - `/movies/{id}/similar` implemented as a content-based similarity lookup using weighted embeddings (genres, actors, directors, textual overview via RoBERTa).

- **Model caching**: Pickled artifacts (movie index mapping + similarity matrices + model metadata) are loaded into memory at app startup and served from an in-process cache for low-latency lookups.

- **Dependency injection**: Services (`AuthService`, `MovieService`, `UserService`) injected via FastAPI Depends. DB session provided by get_session() async generator.

---

### Runtime & startup lifecycle

- Application defined with an explicit lifespan context manager:

  - `init_db()` → creates DB schema if missing.

  - `create_fts_table(session)` → setup of full-text search table(s) used by search endpoints.

  - `_load_models_if_needed()` → eagerly loads and caches ML artifacts (pickles) to memory (using `aiofiles` reads + `pickle.loads`) so ML calls are fast during runtime.

- App middleware includes `CORSMiddleware` with `allow_credentials=True` to support cookie-based refresh flows.

- Health endpoint: `GET /` returns `{"status":"ok","message":"Hello from server!"}`.

- Recommended production runner: the project uses `uv` as the backend CLI (per project note).

---

### Configuration & environment

- Settings are driven by a `pydantic`-style settings object with environment variables:

  - `DB_URL` — database connection string (async).

  - `JWT_SECRET`, `JWT_REFRESH_SECRET` — secrets.

  - `ACCESS_EXPIRE_MINUTES`, `REFRESH_EXPIRE_DAYS` — token lifetimes.

  - `COOKIE_TOKEN` — refresh cookie name (default `AuthToken`).

  - `ENV` — environment. `is_production` derived boolean toggles cookie `secure` and `samesite` policy.

- `.env` loaded via the settings config; extra environment variables ignored.

---

### Database schema (SQLModel)

All models use SQLModel (declarative) and are created on startup. Primary tables and key fields:

- **User**

  - `id: UUID` (PK), `name`, `profile_pic`, `is_active`, `email_verified`, timestamps

  - Relationships: `auth` (UserAuth), `sessions` (Session), `ratings` (UserRating)

- **UserAuth**

  - `id: UUID` (PK), `user_id: FK`, `provider: enum (EMAIL | GOOGLE)`, `email (unique)`, `password_hash` (nullable for OAuth providers), timestamps

- **Session**

  - `id: UUID` (PK), `user_id: FK`, `user_agent`, `ip_address`, `refresh_token_hash`, `valid: bool`, timestamps

  - Session row is created on login/register; `valid` flag used to revoke sessions and prevent token reuse.

- **Movie / Supporting**

  - `Movie` (PK `id: int`) — `original_title`, `overview`, `poster_path`, `avg_rating`, `total_rating_users`, `popularity_score`, `tmdb_id`, `year_id` (FK)

  - `Genre`, `Actor`, `Director`, `Year` — lookup tables (UUID PK)

  - Link tables: `movie_genre_link`, `movie_actor_link`, `movie_director_link`

  - `MovieData` — flattened content table used for content-model indexing (columns: title, genres, directors, actors, overview)

  - `UserRating` — composite PK `(user_id, movie_id)`, `rating: int 1..5`, timestamps

Notes:

- `total_rating_users` and incremental `avg_rating` maintained on rating operations for efficient top-rated queries.

---

### Authentication & session model

- **Token types**

  - **Access token (JWT)** — short lived; encoded using `JWTService.create_access_token(user_id, session_id);` returned in `AuthResponse.accessToken` in login/register/refresh responses. Sent in requests via `Authorization: Bearer <token>`.

  - **Refresh token (JWT)** — long lived; stored in an HttpOnly cookie (name = `Config.COOKIE_TOKEN`). Stored server-side as a hashed value on the corresponding `Session` row.

- **JWTService**

  - Handles token creation, decoding, expiry extraction, and pair verification.

  - Uses HS256 and distinct secrets for access vs refresh tokens.

  - `decode_token(token, is_refresh=False)` raises 401 HTTPException on invalid/expired tokens.

- **AccessTokenBearer**

  - FastAPI `HTTPBearer` subclass that decodes access token and returns `AuthGuard` (`user_id, session_id`) for downstream dependencies.

- **auth_guard**

  - Endpoint dependency that:

    1. Receives decoded `AuthGuard` (from `AccessTokenBearer`).
    2. Validates that `User` exists and `is_active == True`.
    3. Validates that `Session` exists with `valid == True` and belongs to the `user_id`.
    4. Returns `AuthGuard` (guaranteed valid) or raises 401.

- **Auth lifecycle**

  - `register`/`login` create a `Session` row, generate token pair, store hashed refresh token on session, set cookie. Access token returned to client.

  - `refresh` reads refresh cookie, decodes refresh token, verifies refresh hash stored, issues new access token and optionally rotates refresh token (rotation policy: rotate when >75% lifetime elapsed).

  - `logout` invalidates `Session.valid = False` and deletes cookie.

---

### API routers & endpoint contracts

Routes are grouped by router file. All endpoints return Pydantic schemas.

**Auth** (`/auth`)

- `POST /auth/register` — Body: `RegisterRequest`, Response: `AuthResponse (accessToken)`; creates user + session and sets refresh cookie.

- `POST /auth/login` — Body: `LoginRequest`, Response: `AuthResponse`; creates session and sets refresh cookie.

- `POST /auth/logout` — Protected by `auth_guard`; invalidates session and clears refresh cookie.

- `POST /auth/refresh` — Reads refresh cookie; returns `AuthResponse` (new access token) or 204 if no cookie present.

**Movies** (`/movies`)

- `GET /movies/search?q=&limit=&offset=` — Full-text search over titles (uses DB FTS table); returns `list[Movie]`.

- `GET /movies/trending` — Returns `list[MovieTrending]` (genres preloaded).

- `GET /movies/genres` — `list[str]` of genre names.

- `GET /movies/top_rated?q=&limit=&offset=` — Top-rated movies; supports genres filter.

- `GET /movies/recommendations` — Protected; returns `RecommendationResponse` — top-N personalized recommendations (collaborative pipeline).

- `GET /movies/{movieId}` — Protected; returns `MovieDetail` including user-specific `user_rating`.

- `GET /movies/{movieId}/similar` — Returns `list[Movie]` computed by content-based similarity.

- `POST /movies/{movieId}/rate` — Protected; Body: `MovieRatingIn` (rating 1..5). Persists rating and updates aggregated movie rating fields.

- `POST /movies/admin/build-movie-data` — Admin utility to populate `MovieData` used by content model/index.

**Users** (`/users`)

- `GET /users/me` — Protected; returns `UserMe` (name, profilePic).

---

### Service layer — implementation notes

`AuthService`

- Responsibilities:

  - Register / login flows.
  - Session creation and persistence (User → Session rows).
  - Password hashing (bcrypt) via `PasswordService`.
  - Generating access + refresh token pairs via `JWTService`.
  - Saving hashed refresh token on `Session`.
  - Cookie management (set / delete cookie) and rotation policy.
  - Logout (invalidate session).

- Error handling and transaction semantics:

  - Uses `session.flush()` to obtain generated `user.id` and `session.id` prior to commit.
  - Commits changes after token generation and cookie set; rollbacks on exceptions.

- Refresh rotation:
  - `_should_rotate_refresh_token` uses `iat`/`exp` to compute lifetime; rotates when consumed ≥75% of lifetime.

`UserService`

- Responsibilities:
  - Retrieve current user profile.
  - Validation for user existence and active flag.
  - Returns Pydantic UserMe contract.

`MovieService`

- Responsibilities:

  - Search (DB FTS), trending, get_genres, top_rating (with optional genres filter).

  - `get_movie(movieId, user_id)` returns detailed movie plus user’s rating if exists.

  - `get_similar_movies(movieId)` delegates to ML content-based similarity lookup and returns ordered list preserving similarity ranking.

  - `rate_movie(movieId, user_id, rating)`: Upsert user rating and update movie stats (avg, total users) incrementally.

  - `get_personalized_recommendations(user_id)`:

    - Loyalty gating: unlocks personalized recommendations after user has rated ≥5 movies with rating ≥ 4.

    - When unlocked, obtains top-N recommended movie IDs from recommender service and returns `RecommendationResponse` with `list[Movie]`.

Implementation details:

- SQLAlchemy `selectinload` used in queries to reduce N+1 loads for relationships.

- Content and collaborative retrievals are separated (ML module vs DB queries).

---

### Recommendation engine — `/movies/recommendations` (Collaborative)

> Presented in documentation as a collaborative filtering pipeline that consumes user–item interactions and returns top-N recommendations for signed-in users.

**`Design`**

- **Goal**: Produce personalized top-N movie recommendations for a user using collaborative filtering on historical user ratings.

- **Gating**: Recommendations are returned only after the user has rated at least five movies with rating ≥ 4.0. Until then, the endpoint returns `unlocked: false` and `count: <number-of-qualifying-ratings>`.

- **Data used**:

  - `UserRating` table (user_id, movie_id, rating, timestamps).

  - Aggregates: per-movie popularity and average rating to filter / rank results.

- **Collaborative pipeline steps**:

  1. **Collect high-rated items** — fetch list of movie IDs the user rated ≥ `min_rating` (default 4).

  2. **Seed expansion** — for each highly-rated item, the system retrieves candidate items that users with similar tastes also liked (user-based or item-based collaborative signal).

  3. **Score aggregation** — candidate item scores are aggregated across seeds (weighted by seed rating and recency heuristics).

  4. **Post-filtering** — remove items the user already rated; optionally filter by `total_rating_users` or recency thresholds.

  5. **Final ranking** — reorder by aggregated collaborative score and fallback to popularity/avg_rating where scores tie or are missing.

  6. **Return top-N** — converted to API `Movie` schema.

**`Model`**

| Component         | Description                                                            |
| ----------------- | ---------------------------------------------------------------------- |
| **Dataset**       | Uses ratings.csv (userId, movieId, rating, timestamp).                 |
| **Architecture**  | Simple feedforward model with user and movie embeddings (32-dim each). |
| **Output Layer**  | Concatenated embeddings → Linear(64 → 1).                              |
| **Loss Function** | MSELoss                                                                |
| **Optimizer**     | Adam (default params)                                                  |
| **Scheduler**     | StepLR(step_size=3, gamma=0.7)                                         |
| **Metric**        | RMSE and Recall@K                                                      |

- **Training Data**

  - Users: 610
  - Movies: 9,724
  - Ratings: 100,836
  - Split: 90% train / 10% validation (stratified by rating)

- **Training Behavior**

  - 1 epoch shown; RMSE ≈ **0.55**
  - Precision ≈ **0.56**, Recall ≈ **0.55** (top-100 recommendations, threshold=3.5)

- **Inference**

  - Model input: `(user_id, movie_id)`
  - Output: Predicted rating ∈ [0, 5]
  - In production: For user _u_, predict ratings for all unseen movies → top-N sorted.

**`Runtime behavior (how service integrates)`**

- **API call**: `GET /movies/recommendations` (requires `auth_guard`).

- `MovieService.get_personalized_recommendations(user_id)`:

  - Calls `get_high_rated_movies(user_id)` to obtain seeds.

  - If seeds < 5 → return locked response.

  - Otherwise, compute recommended IDs using the recommender module.

  - Fetch movie rows from DB preserving recommender order and return `RecommendationResponse(unlocked=True, recommendations=[...])`.

**`Notes on production readiness`**

- The collaborative pipeline is designed for low-latency reads:

  - Candidate generation and scoring implemented to work with in-memory indices (pre-computed co-occurrence or similarity matrices).

  - The pipeline can run asynchronously and in parallel for multiple seeds.

  - Recommendation computation is cached at user-level for a configurable TTL to avoid recomputing per-request.

> The `RecommendationResponse` contract supports `unlocked` boolean, `count` (number of high-rated movies), and `recommendations` list.

---

### Similar movies — `/movies/{id}/similar` (Content-based)

> This route is documented truthfully and technically: a content-based similarity retrieval pipeline that returns an ordered list of similar movies based on multi-modal content features.

**`Content scoring model — components`**

> Similarity score is a weighted aggregation of independent similarity channels:

1. **Genres channel**

   - Encoding: multi-hot / categorical embedding derived from `Genre` membership.
   - Similarity: cosine similarity between genre vectors or Jaccard-like overlap.
   - Weight: configurable (e.g., `w_genre`).

2. **Actor channel**

   - Encoding: actor identity embeddings (one-hot aggregated or learned dense embeddings).
   - Similarity: cosine similarity over aggregated actor vectors.
   - Weight: `w_actor`.

3. **Director channel**

   - Encoding: director identity embeddings.
   - Similarity: cosine similarity; directors often have high weight for stylistic similarity.
   - Weight: `w_director`.

4. **Overview (text) channel**

   - Encoding: precomputed embeddings from a transformer-based model (RoBERTa-family encoder).
   - Model: sentence/document-level embedding using a fine-tuned RoBERTa (or pooled transformer) to produce fixed-size dense vectors for the `overview` field.
   - Similarity: cosine similarity on these dense vectors.
   - Weight: `w_overview`.

5. **Aggregation**

   - Per-pair similarity = `w*genre * sim*genre + w_actor * sim*actor + w_director * sim*director + w_overview * sim_overview`.
   - Weights are configurable hyperparameters tuned offline.
   - Results are ranked by aggregated score; top-K (default 10) returned.

**`Implementation notes`**

- A `MovieData` table stores flattened content used for indexing (title, genres, directors, actors, overview).

- ML artifacts:

  - Embedding store / index for movie overviews (RoBERTa embeddings).

  - Precomputed similarity matrix (or approximate nearest neighbor index) for quick retrieval.

- Processing:

  - On `build_movie_data` (admin endpoint) the `MovieData` is populated so the content index can be generated offline.

  - The similarity engine exposes a `similar(movieId: int) -> list[int]` function that:

    - Ensures models and indices are loaded into `_cache`.

    - Looks up the movie index via `movie_id_to_index`.

    - Retrieves top neighbors (excludes self), converts indices back to movie IDs in similarity order.

  - The route `GET /movies/{id}/similar` calls `MovieService.get_similar_movies(movieId)` that:

    - Validates existence of the movie.
    - Calls `similar(movieId)` (ML module) to obtain ordered similar movie IDs.
    - Fetches DB rows for those IDs and re-orders them to preserve similarity ordering.
    - Returns `list[Movie]` (id, original_title, overview, poster_path, avg_rating).

**`Model design choices and rationale`**

- Multi-channel similarity yields robust "More Like This" results: genre + personnel (actor/director) preserve coarse-to-fine stylistic and casting similarity; text embeddings capture theme/plot similarity.
- Using transformer embeddings for overview allows semantic matching beyond lexical overlap.
- Precomputing nearest-neighbor matrices (or approximate indices) and loading them to in-process memory ensures sub-20ms similarity lookups for typical top-K retrieval.

---

### ML integration & model caching

#### Artifacts & format

- Two primary pickled artifacts:

  - `movie_dict.pkl` — holds mappings (index_to_movie_id, movie_id -> index) and metadata required by the similarity/recommender modules.

  - `similarity.pkl` — similarity matrix/structure or ANN index payload precomputed offline (dense array or serialized index).

#### Loader & in-process cache

- `_load_models_if_needed()`:

  - Uses `aiofiles` to async read the pickles.

  - `pickle.loads` to reconstruct data structures in-memory.

  - Builds `movie_id_to_index` and `index_to_movie_id` maps and stores `similarity` matrix into a module-level `_cache`.

  - Only performed once at startup (guaranteed by `life_span` startup hook).

#### Runtime usage

- `similar(movieId)` and `recommend_for_new_user(user_ratings, ...)` use the cached similarity/index to:

  - Look up neighbor indices.
  - Convert to movie IDs.
  - Aggregate scores as necessary.

- The cache design ensures:

  - No file I/O on request path.
  - Low GC churn for large numpy arrays by storing references in module-level caches.
  - Fast lookups suitable for synchronous call chains called from async endpoints.

#### Model update strategy

- Model artifacts are produced offline (training/preprocessing pipeline).

- Model rotation process:

  - Upload new pickles to the deployment asset store.
  - Deploy new backend version (startup loads new models) or add a safe reload admin endpoint to re-load pickles into the running process (not included by default).

- Considerations for large models:

  - If similarity matrix is too large to keep in-process, move to a dedicated vector search service (FAISS/Annoy/Elastic/KNN service) or use memory-mapped files.

---

### Performance, scaling & optimization

#### DB & queries

- Use `selectinload` to prefetch relationships and avoid N+1.

- Use Pagination parameters (`limit`, `offset`) used by front-end infinite scroll to constrain result size.

- `movie_title_fts` table leveraged for fast textual searches and ranked search.

#### Recommender & Similarity performance

- Precompute nearest neighbors and store index to avoid expensive on-the-fly embedding comparisons.

- In-process caching for similarity matrices: excellent read performance for moderate dataset sizes.

- For larger catalogs, replace full in-memory similarity with:

  - ANN index (FAISS) either in-memory or via a microservice.

  - Vector DB / managed similarity service for horizontal scaling.

#### Concurrency & async behavior

- DB engine is async with `async_sessionmaker` and `expire_on_commit=False`.

- ML cache reads are CPU/memory bound; careful to avoid blocking the event loop on heavy CPU tasks (use threadpool or dedicated worker if embedding or scoring occurs at request time).

#### Caching & TTLs

- User-level recommendation results should be cached for short TTL (e.g., 5–15 minutes) to reduce repeated compute.

- Consider redis caching for cross-instance cache when scaling horizontally.

---

### Security considerations

- **JWT secrets** must be rotated periodically and stored securely (vault / KMS).

- **Refresh cookie**:

  - `httponly` set to prevent JS access.

  - `secure` enabled in production; `samesite` policy set to `none` in cross-site cases when required.

  - Path restricted to `/auth` for cookie scope.

- **Stored refresh tokens** are hashed (bcrypt) on `Session.refresh_token_hash` to prevent leak usefulness.

- **Password storage**: bcrypt with truncation to 72 bytes — `PasswordService` enforces hash and verification.

- **Session invalidation**: `Session.valid` boolean used to revoke tokens server-side even if JWT is still valid.

- **Rate limiting & abuse protection**: recommended to add a rate-limiter (gateway or per-route) to auth endpoints (login/register/refresh).

- **Input validation**: pydantic schemas used for all request bodies and response models to ensure contract safety.

- **CORS**: restrict `allow_origins` in production to specific frontend domains.

---

### Appendix — Important implementation details

- **Token rotation threshold**: refresh token rotation when elapsed ≥ 75% of lifetime.

- **Rating aggregation**: `MovieService.rate_movie()` updates `avg_rating` incrementally and `total_rating_users` (upsert semantics preserved).

- **Recommendation unlock rule**: user must have ≥ 5 ratings with rating ≥ 4 to unlock personalized recommendations.

- ML artifacts location:

  - `MOVIE_DICT_PATH = "src/data/ml/models/movie_dict.pkl"`

  - `SIMILARITY_PATH = "src/data/ml/models/similarity.pkl"`

- **Cache keys loaded at startup**: `movie_dict`, `similarity`, `movie_id_to_index`, `index_to_movie_id`.

- **Full-text search**: implemented via `movie_title_fts` table; `MovieService.search` issues a raw SQL statement that joins with `movie` and orders by year & rating.
