import { useEffect, useRef, useState } from "react";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";
import { Skeleton } from "@/components/ui/skeleton";
import type { MovieTrending } from "@/types";
import Autoplay from "embla-carousel-autoplay";
import { Star, StarHalf } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import useAuth from "@/hooks/use-auth";
import MovieModel from "./movieModel";
import { Link } from "wouter";

export default function Trending() {
  const auth = useAuth();
  const [movies, setMovies] = useState<MovieTrending[]>([]);
  const [loading, setLoading] = useState(true);
  const autoplayRef = useRef(
    Autoplay({ delay: 5000, stopOnInteraction: false })
  );
  const [selectedMovie, setSelectedMovie] = useState<MovieTrending | null>(
    null
  );
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const res = await fetch(
          `${import.meta.env.VITE_API_URL}/movies/trending`
        );
        if (!res.ok) throw new Error("Failed to fetch trending movies");
        const data = await res.json();
        setMovies(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTrending();
  }, []);

  const handleOpenDetails = (movie: MovieTrending) => {
    if (auth?.isAuth) {
      setSelectedMovie(movie);
      setIsOpen(true);
      console.log(movie);
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

  if (loading) {
    return (
      <div className="flex gap-3 overflow-hidden p-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="w-[873px] h-[522px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <>
      <section className="w-full flex justify-center px-2 py-1">
        <div className="relative w-full max-w-[1280px] h-[522px]">
          <Carousel
            opts={{
              loop: true,
              align: "center",
              containScroll: "trimSnaps",
              slidesToScroll: 1,
            }}
            plugins={[autoplayRef.current]}
            className="h-full w-full"
          >
            <CarouselContent className="h-full w-full -ml-2">
              {movies.map((movie) => {
                const rating = movie.avg_rating;
                const fullStars = Math.floor(rating);
                const hasHalf = rating - fullStars >= 0.5;
                const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0);

                return (
                  <CarouselItem key={movie.id} className="flex-none relative">
                    <div className="overflow-hidden shadow-lg border border-border">
                      {/* Poster + Overlay */}
                      <div className="relative w-[818px] h-[522px] overflow-hidden">
                        <img
                          src={movie.poster_path}
                          alt={movie.original_title}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/60 to-transparent" />

                        <img
                          src={movie.poster_path}
                          alt={movie.original_title}
                          className="absolute top-0 right-0 h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/30 to-transparent" />

                        {/* Content */}
                        <div className="absolute bottom-0 left-0 right-0 p-4 sm:p-6 md:p-8 bg-gradient-to-t from-black/90 via-transparent to-transparent">
                          <div className="grid md:grid-cols-3 gap-6 md:gap-8">
                            <div className="md:col-span-2 space-y-2 md:space-y-2">
                              <div className="text-white flex">
                                <h3 className="text-2xl font-semibold drop-shadow-md">
                                  {movie.original_title}
                                </h3>
                                <span className="px-2 py-1 border border-muted-foreground/30 rounded text-[10px] sm:text-xs text-muted-foreground mt-1 ml-3">
                                  {movie.year}
                                </span>
                              </div>

                              {/* Stars */}
                              <div className="flex items-center gap-2 text-white">
                                {Array.from({ length: fullStars }).map(
                                  (_, i) => (
                                    <Star
                                      key={`full-${i}`}
                                      className="w-4 h-4 fill-yellow-400 stroke-yellow-400"
                                    />
                                  )
                                )}
                                {hasHalf && (
                                  <StarHalf
                                    key="half"
                                    className="w-4 h-4 fill-yellow-400 stroke-yellow-400"
                                  />
                                )}
                                {Array.from({ length: emptyStars }).map(
                                  (_, i) => (
                                    <Star
                                      key={`empty-${i}`}
                                      className="w-4 h-4 stroke-yellow-400"
                                    />
                                  )
                                )}
                                <span className="font-bold text-sm">
                                  {movie.avg_rating}
                                </span>
                              </div>

                              {/* Genres */}
                              <div>
                                <span className="text-muted-foreground">
                                  Genres:{" "}
                                </span>
                                <div className="flex flex-wrap gap-2 mt-2">
                                  {movie.genres.map((g) => (
                                    <span
                                      key={g}
                                      className="px-2 sm:px-3 py-1 rounded-md text-[10px] sm:text-xs bg-[#262626] text-[#fafafa] transition-colors"
                                    >
                                      {g}
                                    </span>
                                  ))}
                                </div>
                              </div>

                              {/* Overview */}
                              <p className="text-sm sm:text-base text-white leading-relaxed line-clamp-2">
                                {movie.overview}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="absolute bottom-4 right-4">
                          <Button
                            variant="secondary"
                            size="lg"
                            className="rounded-lg shadow-lg bg-[#e5e5e5] text-[#171717] hover:bg-[#e5e5e5]/90 transition-colors"
                            onClick={() => handleOpenDetails(movie)}
                          >
                            View Details
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CarouselItem>
                );
              })}
            </CarouselContent>
          </Carousel>
        </div>
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
