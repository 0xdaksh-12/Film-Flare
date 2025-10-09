import { useEffect, useRef, useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import type { Movie, MovieDetail, MovieTrending } from "@/types";
import { Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import Scroller from "@/components/ui/scroller";
import { apiAuth } from "@/lib/api";
import MovieCard from "../ui/movie-card";

interface MovieDetailsProps {
  movie: Movie | MovieDetail | MovieTrending;
  isOpen: boolean;
  onClose: () => void;
  onMovieSelect: (movie: MovieDetail) => void; // always return full detail
}

export default function MovieModel({
  movie,
  isOpen,
  onClose,
  onMovieSelect,
}: MovieDetailsProps) {
  const [details, setDetails] = useState<MovieDetail | null>(
    "actors" in movie ? (movie as MovieDetail) : null
  );
  const [userRating, setUserRating] = useState<number>(
    "user_rating" in movie && movie.user_rating ? movie.user_rating : 0
  );
  const [similarMovies, setSimilarMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(!details);
  const [fromSimilar, setFromSimilar] = useState(false);
  const similarRef = useRef<HTMLDivElement>(null);
  const [submittingRating, setSubmittingRating] = useState(false);
  const previousRating = useRef<number>(0);

  useEffect(() => {
    setDetails(null);
    setSimilarMovies([]);
  }, [movie.id]);

  useEffect(() => {
    if (!isOpen) return;

    const fetchDetails = async () => {
      try {
        setLoading(true);
        const { data } = await apiAuth.get<MovieDetail>(`/movies/${movie.id}`);
        setDetails(data);
        setUserRating(data.user_rating ?? 0);
        previousRating.current = data.user_rating ?? 0;
      } catch (err) {
        console.error("Failed to fetch movie details:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [isOpen, movie.id]);

  useEffect(() => {
    if (!isOpen) return;

    const fetchSimilar = async () => {
      try {
        const { data } = await apiAuth.get<Movie[]>(
          `/movies/${movie.id}/similar`
        );
        setSimilarMovies(data);
      } catch (err) {
        console.error("Failed to fetch similar movies:", err);
        setSimilarMovies([]);
      }
    };

    fetchSimilar();
  }, [isOpen, movie.id]);

  useEffect(() => {
    if (fromSimilar && details && !loading && similarRef.current) {
      requestAnimationFrame(() => {
        similarRef.current?.scrollIntoView({
          behavior: "auto",
          block: "start",
        });
      });
      setFromSimilar(false);
    }
  }, [details, loading, fromSimilar]);

  if (!isOpen) return null;

  const submitRating = async () => {
    if (userRating === 0 || userRating === previousRating.current) return;
    try {
      setSubmittingRating(true);
      await apiAuth.post(`/movies/${movie.id}/rate`, { rating: userRating });
      const { data } = await apiAuth.get<MovieDetail>(`/movies/${movie.id}`);
      setDetails(data);
      setUserRating(data.user_rating ?? 0);
      previousRating.current = data.user_rating ?? 0;
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingRating(false);
    }
  };

  const handleSimilarClick = async (m: Movie) => {
    setFromSimilar(true);
    try {
      const { data } = await apiAuth.get<MovieDetail>(`/movies/${m.id}`);
      onMovieSelect(data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        key={movie.id}
        className="max-w-4xl p-6 rounded-2xl min-w-[825px] max-h-[530px] flex flex-col"
      >
        {loading ? (
          <>
            <div className="flex flex-row justify-between items-start bg-background z-10">
              <div>
                <Skeleton className="h-8 w-64 mb-2" />
                <div className="flex flex-wrap gap-2">
                  <Skeleton className="h-6 w-20" />
                  <Skeleton className="h-6 w-24" />
                </div>
              </div>
              <div className="flex items-center gap-2 mr-4">
                <Skeleton className="h-8 w-12" />
                <Skeleton className="h-8 w-12" />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto">
              <div className="flex flex-col md:flex-row gap-6 my-4">
                <Skeleton className="w-[260px] h-[390px] rounded-lg" />
                <div className="flex-1 space-y-4">
                  <Skeleton className="h-5 w-3/4" />
                  <Skeleton className="h-32 w-full" />
                  <Skeleton className="h-5 w-1/2" />
                  <Skeleton className="h-5 w-full" />
                  <Skeleton className="h-5 w-3/4" />
                  <div className="flex gap-2 items-center">
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((_, i) => (
                        <Skeleton key={i} className="w-6 h-6 rounded" />
                      ))}
                    </div>
                    <Skeleton className="h-9 w-24" />
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          details && (
            <>
              {/* Header */}
              <div className="flex flex-row justify-between items-start z-10 bg-transparent">
                <div className="flex-1">
                  <div className="text-2xl font-semibold mb-2">
                    {details.original_title}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {details.genres.map((genre) => (
                      <span
                        key={genre}
                        className="px-3 py-1 rounded-full bg-secondary text-sm"
                      >
                        {genre}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2 mr-4">
                  <span className="text-2xl font-mono text-blue-600">
                    {details.avg_rating?.toFixed(1) || "N/A"}
                  </span>
                  <span className="text-2xl font-semibold">/ 5</span>
                </div>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto">
                <div className="flex flex-col md:flex-row gap-6">
                  <img
                    src={details.poster_path}
                    alt={details.original_title}
                    className="w-[260px] h-[390px] rounded-lg object-cover flex-shrink-0"
                  />
                  <div className="flex-1 space-y-2 -mt-2">
                    <h4 className="font-semibold text-lg mb-1">
                      About the Movie
                    </h4>
                    <p className="text-sm text-muted-foreground leading-relaxed text-justify mr-4">
                      {details.overview}
                    </p>

                    {details.actors.length > 0 && (
                      <>
                        <h5 className="font-semibold mb-1 text-base">Actors</h5>
                        <p className="text-sm text-muted-foreground">
                          {details.actors.join(", ")}
                        </p>
                      </>
                    )}

                    {details.directors.length > 0 && (
                      <>
                        <h5 className="font-semibold mb-1 text-base">
                          Director
                        </h5>
                        <p className="text-sm text-muted-foreground">
                          {details.directors.join(", ")}
                        </p>
                      </>
                    )}

                    {/* Rating Section */}
                    <div className="mt-4">
                      <h4 className="font-semibold text-lg mb-2">
                        Rate this Movie
                      </h4>
                      <div className="flex items-center gap-2">
                        <div className="flex gap-1">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <Star
                              key={star}
                              className={`w-6 h-6 cursor-pointer transition-colors ${
                                star <= userRating
                                  ? "text-yellow-500 fill-yellow-500"
                                  : "text-gray-300"
                              }`}
                              onClick={() => setUserRating(star)}
                            />
                          ))}
                        </div>
                        {userRating !== 0 &&
                          userRating !== previousRating.current && (
                            <Button
                              onClick={submitRating}
                              variant="secondary"
                              size="sm"
                              className="ml-2"
                            >
                              {submittingRating ? "Submitting..." : "Submit"}
                            </Button>
                          )}
                      </div>
                    </div>
                  </div>
                </div>

                <hr className="border-border my-4" />

                {/* More Like This */}
                <div ref={similarRef}>
                  <h2 className="font-bold text-2xl mb-3">More Like This</h2>
                  {similarMovies.length === 0 ? (
                    <div className="flex gap-4 overflow-hidden p-2">
                      {Array.from({ length: 6 }).map((_, i) => (
                        <Skeleton
                          key={i}
                          className="w-[230px] h-[340px] rounded-xl flex-shrink-0"
                        />
                      ))}
                    </div>
                  ) : (
                    <Scroller className="p-2">
                      {similarMovies.map((similarMovie) => (
                        <div
                          key={similarMovie.id}
                          className="flex-shrink-0 w-[230px] transition-transform hover:scale-[1.02] cursor-pointer"
                          onClick={() => handleSimilarClick(similarMovie)}
                        >
                          <MovieCard movie={similarMovie} onOpen={() => {}} />
                        </div>
                      ))}
                    </Scroller>
                  )}
                </div>
              </div>
            </>
          )
        )}
      </DialogContent>
    </Dialog>
  );
}
