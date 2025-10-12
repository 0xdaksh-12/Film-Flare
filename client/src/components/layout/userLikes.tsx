import { useEffect, useState } from "react";
import type { Movie, RecommendationResponse } from "@/types";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "wouter";
import useAuth from "@/hooks/use-auth";
import { toast } from "sonner";
import Scroller from "@/components/ui/scroller";
import MovieCard from "../ui/movie-card";
import MovieModel from "./movieModel";
import { apiAuth } from "@/lib/api";

export default function UserLikes() {
  const auth = useAuth();
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [lockedMessage, setLockedMessage] = useState<string | null>(null);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  // Fetch user-specific recommendations
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!auth?.isAuth) return; // don’t fetch if not logged in

      try {
        setLoading(true);
        const { data } = await apiAuth.get<RecommendationResponse>(
          `/movies/recommendations`
        );

        if (!data.unlocked) {
          setLockedMessage(
            `Rate ${
              5 - (data.count ?? 0)
            } more movies to unlock personalized recommendations.`
          );
          setMovies([]); // clear previous data
        } else {
          setMovies(data.recommendations ?? []);
          setLockedMessage(null);
        }
      } catch (err) {
        console.error("Failed to fetch recommendations", err);
        toast.error("Something went wrong while loading recommendations.");
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [auth?.isAuth]);

  const handleOpenMovie = (movie: Movie) => {
    if (auth?.isAuth) {
      setSelectedMovie(movie);
      setIsOpen(true);
    } else {
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
    }
  };

  return (
    <>
      <section className="px-5 py-6 space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h2 className="font-bold text-3xl">You Might Like</h2>
          {auth?.isAuth && lockedMessage && (
            <span className="text-sm text-muted-foreground">
              {lockedMessage}
            </span>
          )}
        </div>
        <hr className="border-border" />

        {/* Content */}
        {loading ? (
          <div className="flex gap-4 overflow-hidden p-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton
                key={i}
                className="w-[230px] h-[340px] rounded-xl flex-shrink-0"
              />
            ))}
          </div>
        ) : lockedMessage ? (
          <div className="text-center text-muted-foreground py-10 text-lg">
            {lockedMessage}
          </div>
        ) : movies.length > 0 ? (
          <Scroller className="p-2 flex gap-4">
            {movies.slice(0, 20).map((movie) => (
              <div
                key={movie.id}
                className="flex-shrink-0 w-[230px] transition-transform hover:scale-[1.02]"
              >
                <MovieCard
                  movie={movie}
                  onOpen={() => handleOpenMovie(movie)}
                />
              </div>
            ))}
          </Scroller>
        ) : (
          <p className="text-center text-muted-foreground py-10 text-lg">
            No recommendations yet.
          </p>
        )}
      </section>

      {selectedMovie && (
        <MovieModel
          movie={selectedMovie}
          isOpen={isOpen}
          onClose={() => {
            setIsOpen(false);
            setSelectedMovie(null);
          }}
          onMovieSelect={setSelectedMovie}
        />
      )}
    </>
  );
}
