"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import { SearchFilterBar } from "@/components/search-filter-bar";
import { Avatar } from "@/components/ui/avatar";
import { cn } from "@/lib/cn";
import { communityPosts } from "@/lib/mock-data";
import type { CommunityPost, SelectOption } from "@/lib/types";

const sortOptions: SelectOption[] = [
  { label: "Newest", value: "newest" },
  { label: "Most liked", value: "liked" },
];

function countryOf(place: string) {
  return place.split(",").pop()?.trim() ?? place;
}

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});

export function CommunityFeed() {
  const [search, setSearch] = useState("");
  const [country, setCountry] = useState("all");
  const [order, setOrder] = useState("newest");
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());

  const countryOptions = useMemo<SelectOption[]>(() => {
    const unique = [...new Set(communityPosts.map((post) => countryOf(post.place)))].sort();
    return [
      { label: "All countries", value: "all" },
      ...unique.map((name) => ({ label: name, value: name })),
    ];
  }, []);

  const posts = useMemo(() => {
    const query = search.trim().toLowerCase();
    const matched = communityPosts.filter((post) => {
      const matchesQuery =
        !query ||
        [post.author, post.place, post.content].some((field) =>
          field.toLowerCase().includes(query),
        );
      const matchesCountry = country === "all" || countryOf(post.place) === country;
      return matchesQuery && matchesCountry;
    });

    const effectiveLikes = (post: CommunityPost) =>
      post.likes + (likedIds.has(post.id) ? 1 : 0);

    const sorted = [...matched];
    if (order === "liked") {
      sorted.sort((a, b) => effectiveLikes(b) - effectiveLikes(a));
    } else {
      sorted.sort((a, b) => b.postedAt.localeCompare(a.postedAt));
    }
    return sorted;
  }, [search, country, order, likedIds]);

  function toggleLike(id: string) {
    setLikedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const searching = search.trim().length > 0;

  return (
    <div className="space-y-6">
      <SearchFilterBar
        search={search}
        onSearchChange={setSearch}
        placeholder="Search a place, traveller or story"
        filter={{ value: country, onChange: setCountry, options: countryOptions }}
        sortBy={{ value: order, onChange: setOrder, options: sortOptions }}
      />

      {posts.length > 0 ? (
        <div className="space-y-5">
          {posts.map((post, index) => (
            <div
              key={post.id}
              className="animate-fade-up"
              style={{ animationDelay: `${Math.min(index, 5) * 60}ms` }}
            >
              <PostCard
                post={post}
                liked={likedIds.has(post.id)}
                onToggleLike={() => toggleLike(post.id)}
              />
            </div>
          ))}
        </div>
      ) : (
        <p className="rounded-2xl border border-dashed border-border px-6 py-12 text-center text-sm text-text-muted">
          {searching
            ? `No stories match "${search.trim()}".`
            : "No stories match those filters."}
        </p>
      )}
    </div>
  );
}

function PostCard({
  post,
  liked,
  onToggleLike,
}: {
  post: CommunityPost;
  liked: boolean;
  onToggleLike: () => void;
}) {
  const likeCount = post.likes + (liked ? 1 : 0);

  return (
    <article className="group overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
      {post.image && (
        <div className="relative h-56 w-full sm:h-64">
          <Image
            src={post.image}
            alt={post.place}
            fill
            sizes="800px"
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-black/10" />

          <button
            type="button"
            onClick={onToggleLike}
            aria-pressed={liked}
            aria-label={liked ? "Unlike this story" : "Like this story"}
            className={cn(
              "absolute top-3 right-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium shadow-sm backdrop-blur-sm transition-all active:scale-95",
              liked
                ? "bg-danger text-white"
                : "bg-white/90 text-text hover:bg-white",
            )}
          >
            <HeartIcon filled={liked} />
            {likeCount}
          </button>

          <div className="absolute inset-x-0 bottom-0 flex items-center gap-3 p-4 text-white">
            <Avatar name={post.author} size="sm" className="ring-2 ring-white/70" />
            <div className="min-w-0">
              <p className="text-sm font-semibold">{post.author}</p>
              <p className="text-xs text-white/80">
                {post.place} ·{" "}
                {dateFormatter.format(new Date(`${post.postedAt}T00:00:00Z`))}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="p-5 sm:p-6">
        <p className="text-sm leading-relaxed text-text">{post.content}</p>
      </div>
    </article>
  );
}

function HeartIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinejoin="round"
      className="size-4"
      aria-hidden
    >
      <path d="M10 17.25c-.24 0-.47-.08-.66-.24C6.1 14.2 3 11.4 3 8.13 3 5.85 4.8 4 7.1 4c1.24 0 2.4.58 3.15 1.5A4.13 4.13 0 0 1 13.4 4C15.7 4 17.5 5.85 17.5 8.13c0 3.27-3.1 6.07-6.34 8.88-.19.16-.42.24-.66.24Z" />
    </svg>
  );
}
