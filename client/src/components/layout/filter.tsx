import { useEffect, useState } from "react";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { X } from "lucide-react";
import Scroller from "../ui/scroller";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

interface FilterProps {
  setFilter: (filters: string[]) => void;
}

export default function Filter({ setFilter }: FilterProps) {
  const [genres, setGenres] = useState<string[]>([]);
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGenres = async () => {
      try {
        const { data } = await api.get("/movies/genres");
        setGenres(data.sort());
      } catch (error) {
        console.error("Failed to fetch genres", error);
      } finally {
        setLoading(false);
      }
    };
    fetchGenres();
  }, []);

  const handleToggle = (value: string[]) => {
    setSelectedGenres(value);
    setFilter(value);
  };

  const sortedGenres = [...genres].sort((a, b) => {
    const aSelected = selectedGenres.includes(a) ? -1 : 1;
    const bSelected = selectedGenres.includes(b) ? -1 : 1;
    if (aSelected !== bSelected) return aSelected - bSelected;
    return a.localeCompare(b);
  });

  return (
    <div className="p-4">
      <Scroller>
        {loading ? (
          <div className="flex gap-2">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton
                key={i}
                className="h-10 w-32 rounded-lg border border-border flex-shrink-0"
              />
            ))}
          </div>
        ) : (
          <ToggleGroup
            type="multiple"
            value={selectedGenres}
            onValueChange={handleToggle}
            className="flex gap-2"
          >
            {sortedGenres.map((genre) => {
              const isSelected = selectedGenres.includes(genre);
              return (
                <ToggleGroupItem
                  key={genre}
                  value={genre}
                  className={`px-4 py-2 rounded-lg border whitespace-nowrap flex items-center gap-2 flex-shrink-0 transition-colors ${
                    isSelected ? "bg-primary text-primary-foreground" : ""
                  }`}
                >
                  {isSelected && (
                    <X
                      size={16}
                      className="ml-1 opacity-80 hover:opacity-100"
                    />
                  )}
                  {genre}
                </ToggleGroupItem>
              );
            })}
          </ToggleGroup>
        )}
      </Scroller>
    </div>
  );
}
