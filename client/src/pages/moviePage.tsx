import { useCallback, useEffect, useRef, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import type { Movie, MovieDetail } from "@/types";
import { useSearch, Link } from "wouter";
import useAuth from "@/hooks/use-auth";
import { toast } from "sonner";
import MovieCard from "@/components/ui/movie-card";
import MovieModel from "@/components/layout/movieModel";
import { api } from "@/lib/api";

export default function MoviePage() {
  const auth = useAuth();
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMovie, setSelectedMovie] = useState<
    Movie | MovieDetail | null
  >(null);
  const [openDialog, setOpenDialog] = useState(false);

  // ---- Refs for pagination control ----
  const offsetRef = useRef(0);
  const isFetchingRef = useRef(false);
  const hasMoreRef = useRef(true);
  const isInitialRef = useRef(true);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const fetchMoviesRef = useRef<(() => Promise<void>) | null>(null);

  // ---- Query Parameters ----
  const search = useSearch();
  const params = new URLSearchParams(search);
  const query = params.get("search");
  const type = params.get("type") ?? "top_rated";
  const genres = params.get("genres");

  if (!auth) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  const { isAuth } = auth;

  // ---- Fetch Movies ----
  const fetchMovies = useCallback(async () => {
    if (isFetchingRef.current || !hasMoreRef.current) return;

    isFetchingRef.current = true;
    setLoading(true);

    try {
      const limit = isInitialRef.current ? 20 : 5;
      let url = `/movies`;

      if (query) {
        url += `/search?q=${encodeURIComponent(query)}&limit=${limit}&offset=${
          offsetRef.current
        }`;
      } else if (type === "top_rated") {
        url += `/top_rated?limit=${limit}&offset=${offsetRef.current}`;
        if (genres) url += `&q=${encodeURIComponent(genres)}`;
      } else {
        // fallback route
        url += `?limit=${limit}&offset=${offsetRef.current}`;
      }

      const { data } = await api.get<Movie[]>(url);

      if (!Array.isArray(data) || data.length === 0) {
        hasMoreRef.current = false;
        return;
      }

      setMovies((prev) => [
        ...prev,
        ...data.filter((m) => !prev.some((p) => p.id === m.id)),
      ]);

      offsetRef.current += limit;
      isInitialRef.current = false;
    } catch (err) {
      console.error("Error fetching movies:", err);
      hasMoreRef.current = false;
    } finally {
      isFetchingRef.current = false;
      setLoading(false);
    }
  }, [query, type, genres]);

  // ---- Reset and Refetch when filters change ----
  useEffect(() => {
    setMovies([]);
    hasMoreRef.current = true;
    offsetRef.current = 0;
    isInitialRef.current = true;
    fetchMovies();
  }, [query, type, genres, fetchMovies]);

  // ---- Keep ref always updated ----
  useEffect(() => {
    fetchMoviesRef.current = fetchMovies;
  }, [fetchMovies]);

  // ---- Infinite Scroll Observer ----
  useEffect(() => {
    if (!sentinelRef.current) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && fetchMoviesRef.current) {
          fetchMoviesRef.current();
        }
      },
      { threshold: 0.1 }
    );

    observerRef.current.observe(sentinelRef.current);

    return () => {
      observerRef.current?.disconnect();
    };
  }, []);

  // ---- Handle Card Click ----
  const handleCardOpen = (movie: Movie) => {
    if (!isAuth) {
      toast.error("Please login first", {
        description: (
          <Link
            href="/auth/login"
            className="text-primary underline hover:text-primary/80 dark:text-accent"
          >
            Go to Login →
          </Link>
        ),
        duration: 4000,
      });
      return;
    }

    setSelectedMovie(movie);
    setOpenDialog(true);
  };

  return (
    <>
      <div className="flex-1 w-full h-full overflow-hidden box-border p-4 pb-0">
        <div className="w-full h-full overflow-y-auto p-4 mb-20">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {movies.map((movie) => (
              <div key={movie.id} className="movie-card">
                <MovieCard movie={movie} onOpen={() => handleCardOpen(movie)} />
              </div>
            ))}

            {loading &&
              Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="w-[230px] h-[340px] rounded-2xl" />
              ))}
          </div>

          <div ref={sentinelRef} className="h-10" />
        </div>
      </div>

      {selectedMovie && (
        <MovieModel
          movie={selectedMovie}
          isOpen={openDialog}
          onClose={() => {
            setOpenDialog(false);
            setSelectedMovie(null);
          }}
          onMovieSelect={(newMovie) => setSelectedMovie(newMovie)}
        />
      )}
    </>
  );
}
