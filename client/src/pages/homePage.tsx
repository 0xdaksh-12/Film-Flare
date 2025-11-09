import Filter from "@/components/layout/filter";
import TopRated from "@/components/layout/topRated";
import Trending from "@/components/layout/trending";
import { useState } from "react";

export default function HomePage() {
  const [filter, setFilter] = useState<string[]>([]);

  return (
    <>
      <div className="flex flex-col p-4">
        <Trending />
      </div>
      <Filter setFilter={setFilter} />
      <TopRated genre={filter} />
    </>
  );
}
