# FilmFlare — Frontend Technical Documentation

> Formal technical documentation for frontend engineers.
> Covers architecture, component API, data flow, authentication, state management, performance, accessibility, build/run, environment variables, and operational recommendations.

---

## Contents

1. [Overview](#overview)
2. [Project layout & conventions](#project-layout--conventions)
3. [Runtime & environment](#runtime--environment)
4. [Authentication (client)](#authentication-client)
5. [API clients](#api-clients)
6. [Global providers & bootstrapping](#global-providers--bootstrapping)
7. [Routing & navigation](#routing--navigation)
8. [Key UI components & contracts](#key-ui-components--contracts)
9. [Pages and flows](#pages-and-flows)
10. [Client-side data patterns & caching](#client-side-data-patterns--caching)
11. [UX / accessibility considerations](#ux--accessibility-considerations)
12. [Performance & optimizations](#performance--optimizations)

---

## Overview

The FilmFlare frontend is a single-page application (React + Vite) built with:

- React (functional components + hooks)
- Tailwind CSS (utility-first styling)
- `shadcn/ui` style components (cards, dialogs, toggles, etc.)
- `lucide-react` for icons
- `wouter` for client-side routing (lightweight, hook-based)
- `axios` for HTTP (`api` & `apiAuth` clients)
- `sonner` for toast notifications
- `next-themes` for theme switching (light/dark)
- TypeScript types under `@/types`

The frontend provides a consumer UI for the backend FilmFlare API. It focuses on fast browsing, infinite scroll, modal details, and lightweight personalization.

---

## Project layout & conventions

Common file locations / conventions (based on provided code):

- `src/`

  - `components/` — shared UI primitives and layout components

    - `ui/` — design system primitives (Button, Input, Card, Dialog, Skeleton, ToggleGroup, Carousel, etc.)
    - `layout/` — page-level components (Header, Trending, TopRated, UserLikes, Filter, MovieModel)
    - `ui/movie-card.tsx`, `ui/scroller.tsx`, etc.

  - `pages/` or `pages-like/` — route pages (`HomePage`, `MoviePage`, `LoginPage`, `RegisterPage`)
  - `context/` — `authContext.tsx`
  - `provider/` — `authProvider.tsx`
  - `hooks/` — `use-auth.ts`, `use-debounce.ts`
  - `lib/` — `api.ts` (`api`, `apiAuth` axios instances), utilities (`cn.ts`)
  - `types/` — TypeScript contracts
  - `App.tsx` — application bootstrap (ThemeProvider, AuthProvider, Toaster, Routes)
  - `routes.tsx` — application route definitions (wouter)

- Styling: Tailwind utility classes; component-level classes follow BEM-ish naming (e.g., `.movie-card` with fixed sizes).

Naming conventions:

- Files / components use PascalCase for React components.
- Hooks in `/hooks` use `useX` naming.
- API clients in `lib` use `api` (no credentials) and `apiAuth` (with credentials).

---

## Runtime & environment

**Environment variables**

- `VITE_API_URL` — base URL for the backend API used by `api` and `apiAuth`.

**Dev / build commands**

- Development: `pnpm dev` (project default)
- Build: `pnpm build`
- Preview / production serve: `pnpm preview` or serve static built output via a static host

**Notes**

- Frontend expects backend to expose `/auth/*` endpoints for auth flows and cookie-based refresh (HttpOnly cookie).
- `apiAuth` uses `withCredentials: true` to include refresh cookie when calling `/auth/refresh` and other protected endpoints.

---

## Authentication (client)

Auth architecture (client side):

- `AuthProvider` (Context Provider) manages:

  - `token` (access token) persisted to `sessionStorage` under key `"Token"`.
  - `user` (fetched from `/users/me`).
  - `loading` state, and API interceptors.
  - `login`, `register`, `logout` actions.

- Token lifecycle:

  - `token` (access token) is stored in `sessionStorage` and attached to `apiAuth` requests via an interceptor.
  - Refresh flow:

    - On mount, `AuthProvider` calls `apiAuth.post("/auth/refresh")` (with credentials) to attempt to get an access token when none exists.
    - `apiAuth` response interceptor retries the original request by calling `/auth/refresh` and updating `token` on 401 responses (not for `/auth/refresh` requests).

  - Logout calls `/auth/logout` and clears `token`/`user` state.

- Axios interceptor behavior:

  - Request interceptor adds `Authorization: Bearer <token>` for `apiAuth` when `token` is present.
  - Response interceptor attempts token refresh for 401 responses and retries the original request once.
  - The refresh request includes `{ withCredentials: true }` to allow the server to read the refresh cookie.

- Important invariants:

  - Access token ephemeral storage: `sessionStorage` (not localStorage) reduces cross-tab persistence risk.
  - Refresh token is managed by the backend via HttpOnly cookie; frontend never reads it.

---

## API clients

Two axios instances:

1. `api` — unauthenticated requests

   - `baseURL: import.meta.env.VITE_API_URL`
   - standard headers: `Content-Type: application/json`

2. `apiAuth` — authenticated / refresh-capable instance

   - same `baseURL` but `withCredentials: true`
   - intended for endpoints requiring access token and / or refresh cookie

Interceptor pattern (in `AuthProvider`):

- Request interceptor attaches `Authorization` header (`apiAuth`) using `token` from state.
- Response interceptor:

  - On `401` and non-retry: calls `/auth/refresh`, updates token, retries original request with new token (sets `_retry = true` to avoid infinite loops).
  - On refresh failure, clears auth state.

Error extraction:

- `getErrorMessage` extracts human readable strings from Axios errors using `response.data.message | detail | error.message`.

---

## Global providers & bootstrapping

`App` wraps the app with:

- `ThemeProvider` (next-themes) for theme switching
- `AuthProvider` for authentication context
- `Toaster` (sonner) for ephemeral notifications
- `Routes` for wouter-based routing

`AuthProvider` responsibilities:

- Token initialization (attempt refresh on mount)
- Attach Axios interceptors for request/response
- Fetch current user (`/users/me`) after token present
- Expose `login`, `register`, `logout` methods to the app

---

## Routing & navigation

- Router: `wouter`
- Routes defined in `Routes` component:

  - `/` → `HomePage`
  - `/movie` → `MoviePage` (expects query params: `search`, `type`, `genres`)
  - `/auth/login` → `LoginPage` (redirects to `/` if `isAuth`)
  - `/auth/register` → `RegisterPage` (redirects to `/` if `isAuth`)

- Link navigation uses `Link` from `wouter` and `setLocation` hook for programmatic navigation.

---

## Key UI components & contracts

This section lists important components, props, behavior, and edge-cases.

### `Header`

- Props: none.
- Uses `useAuth()` to determine `user` & `isAuth`.
- Search input (debounced 300ms via `useDebounce`) updates `/movie?search=...` route.
- Shows login/register buttons when unauthenticated; shows user dropdown & logout (calls `logout()` from context) when authenticated.
- Accessibility: icons have `aria-label` via Button `aria-label` in `ThemeToggle`; profile avatar includes semantic text.

### `Filter`

- Props:

  - `setFilter: (filters: string[]) => void`

- Behavior:

  - Fetches `/movies/genres` on mount, sorts them.
  - Uses `ToggleGroup` (type `multiple`) to select multiple genres.
  - Exposes `selectedGenres` via `setFilter`.
  - Shows skeletons until genres load.

- UI details:

  - Selected genres rendered first via `sortedGenres` comparator.

### `Trending`

- Fetches `/movies/trending` on mount (plain `fetch`).
- Uses Embla `Carousel` with `embla-carousel-autoplay`.
- Renders poster full-bleed slides with overlay and CTA `View Details` (calls `handleOpenDetails`).
- If user not authenticated, `handleOpenDetails` triggers toast with link to login.

### `TopRated`

- Props:

  - `genre: string[]`

- Calls `/movies/top_rated?q=genres...` when `genre` changes.
- Uses `Scroller` to render a horizontally scrollable list of `MovieCard`s.
- On click of a card, authorizes and opens `MovieModel` modal.

### `UserLikes` (You Might Like)

- Fetches `/movies/recommendations` via `apiAuth`.
- If response `unlocked: false`, shows locked message instructing user to rate more movies; otherwise shows recommendations as `MovieCard`s.
- Shows skeletons while loading, handles errors with toasts.

### `MovieModel` (modal)

- Props:

  - `movie` (Movie | MovieDetail | MovieTrending)
  - `isOpen`, `onClose`, `onMovieSelect`

- On open fetches `/movies/{id}` (apiAuth) for details if not already present.
- Also fetches `/movies/{id}/similar` to populate "More Like This".
- Rating:

  - Renders 5-star clickable UI; on submit calls `POST /movies/{id}/rate` and re-fetches movie detail.
  - Visual submit disabled if rating unchanged or zero.

- Similar click:

  - Clicking a similar card fetches `MovieDetail` for that movie and calls `onMovieSelect` — enabling browsing similar movies inside modal.

### `MovieCard`

- Props:

  - `movie: Movie`
  - `onOpen: () => void`

- Hover behavior:

  - Uses `onMouseMove` to detect center-zone hover and starts a delayed timer (350ms) to reveal the CTA button.
  - `showButton` triggers visual overlay (scale + dim) and reveals `View Details` button.
  - Clicking the card triggers `onOpen` (guarded by auth in parent).

- Accessibility:

  - Use of clickable container requires keyboard affordances (see Accessibility notes).

### `Scroller`

- A horizontal scroll container with:

  - Mouse drag-to-scroll
  - `onMouseDown`, `onMouseMove`, `onMouseUp`, `onMouseLeave`

- Good for cross-device (desktop) UX—touch devices will still have native touch scrolling.

---

## Pages and flows

### `HomePage`

- Composition: `Trending`, `Filter`, `TopRated` (with filter), `UserLikes`.
- Filter state is lifted in `HomePage` (`useState<string[]>([])`) and passed into `TopRated`.

### `MoviePage`

- Supports:

  - `?search=...` — server full-text search endpoint (`/movies/search`)
  - `?type=top_rated` — top rated listing (with `genres` optional)

- Implements infinite scroll:

  - `offsetRef`, `isFetchingRef`, `hasMoreRef`
  - Uses an `IntersectionObserver` on a sentinel element to trigger `fetchMoviesRef.current()`.
  - Uses `limit = 20` for initial load, then `limit = 5` for subsequent loads.

- De-duplicates results by checking `prev.some(p => p.id === m.id)`.

### `Auth pages` (`LoginPage`, `RegisterPage`)

- Use `react-hook-form` + `zod` for schema validation and concise UI errors.
- Login/Register calls `AuthProvider` actions (`login`, `register`) and redirect on success.

---

## Client-side data patterns & caching

- **Token cache**: `sessionStorage` for access token.
- **API caching**: No client-side persistent cache library (e.g., SWR/React Query) used in the current code; data is fetched ad-hoc in components and stored in local state.
- **Short-term caching**: `AuthProvider` obtains and reuses token across requests by axios interceptor.
- **Client-side dedupe**:

  - Infinite scroll ensures de-duplication when appending results.
  - Recommendations / trending endpoints are consumed and stored in component state.

**Recommendation**

- Introduce a lightweight client cache (React Query or SWR) for:

  - automatic dedupe
  - background refetching
  - caching with TTL
  - easier optimistic updates (rating flow)

---

## UX / accessibility considerations

- Visual feedback:

  - Skeleton placeholders across lists and modals give perceived performance.
  - Toast notifications for errors/successes via `sonner`.

- Contrast and semantics:

  - Buttons and inputs use shadcn primitives — retain semantic HTML.
  - Images include `alt` attributes (movie title), which is good for screen readers.

- Focus management:

  - When opening `MovieModel` modal, focus should be trapped in the dialog (shadcn `Dialog` generally handles focus trap).
  - When closing modal, return focus to the opener element.

- Form validation:

  - `react-hook-form` + `zod` ensures client-side validation and error messaging.

---

## Performance & optimizations

- **Image loading**

  - `img` uses `loading="lazy"` on `MovieCard` to defer offscreen images.
  - Consider responsive `srcset` / CDN usage for posters to reduce bandwidth and improve LCP.

- **Bundle size**

  - Keep icon usage limited; `lucide-react` is tree-shakeable but verify import pattern (named imports).

- **Network**

  - Use `apiAuth` interceptor and server-side refresh for token renewal instead of forcing full re-login.
  - Consider using React Query for deduping requests (e.g., multiple components requesting `/movies/trending`).

- **Rendering**

  - Avoid expensive operations in render (e.g., heavy sorts on large arrays). `Filter` pre-sorts genres but uses small lists.

- **Scrolling**

  - `Scroller` drag behavior is implemented client-side and performs well; for mobile, consider native touch improvements.

- **Carousel**

  - Embla carousel is used with autoplay plugin; ensure it is lazy-loading images for large slides.

---

## Security considerations (frontend)

- **Tokens & storage**

  - Access token stored in `sessionStorage`. Refresh handled via HttpOnly cookie created by backend — frontend cannot read refresh token.
  - `apiAuth` sends `withCredentials: true` to allow backend to access refresh cookie.

- **XSS protections**

  - Avoid injecting raw HTML into components. All text content is rendered as text (no `dangerouslySetInnerHTML`).

- **CSRF**

  - Using HttpOnly refresh cookie requires server-side CSRF considerations. The backend paths for refresh should use safe cookie attributes and session binding; frontend should avoid exposing any CSRF token.

- **Input validation**

  - All user inputs are validated client-side with `zod` but must be revalidated server-side (already done in backend).

---

## Operational & deployment notes

- **Frontend build**

  - Use `pnpm build` to produce static assets. Host on static hosting (Netlify, Vercel, S3+CloudFront, etc.).

- **Env config**

  - `VITE_API_URL` must point to the backend base URL. For production, ensure `VITE_API_URL` uses secure `https://`.

- **CORS / Cookies**

  - Backend must allow the production frontend origin in CORS and must issue refresh cookie with `SameSite=None` + `Secure` when frontend and backend are cross-site.
  - Cookie path used by backend is `/auth` — calls to `/auth/refresh` rely on cookie path/domain match.

- **Logging & Sentry**

  - Integrate Sentry or similar for runtime exceptions and user-scoped errors from the frontend.

- **Monitoring**

  - Track critical user flows: login/register, rating submission, recommendations fetching. Use analytic events sparingly.

---

## Appendix: useful snippets & contracts

**API contracts (selected)**

`/movies/recommendations` response (TypeScript type):

```ts
export type RecommendationResponse = {
  unlocked: boolean;
  count?: number;
  recommendations?: Movie[];
};
```

`AuthResponse`

```ts
export interface AuthResponse {
  success: boolean;
  accessToken: string;
}
```

**AuthProvider key behaviors**

- Interceptor adds `Authorization: Bearer <token>` for `apiAuth`.
- Response interceptor will:

  - On 401: call `/auth/refresh` with `{ withCredentials: true }`, set new token, and retry original request.
  - Clear token/user on refresh failure.

**Infinite scroll sentinel**

- Use `IntersectionObserver` on a `div` (`ref={sentinelRef}`) with threshold `0.1` to trigger `fetchMovies()` method stored in a ref for stable identity.

**Debounced search**

- `useDebounce(searchQuery, 300)` is used to avoid frequent navigation while typing. On change, `setLocation(`/movie?search=${encodeURIComponent(debouncedSearch.trim())}`)`.

---
