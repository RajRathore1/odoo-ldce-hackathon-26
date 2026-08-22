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

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});

export function CommunityFeed() {
  const [search, setSearch] = useState("");
  const [order, setOrder] = useState("newest");
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());

  const posts = useMemo(() => {
    const query = search.trim().toLowerCase();
    const matched = communityPosts.filter(
      (post) =>
        !query ||
        [post.author, post.place, post.content].some((field) =>
          field.toLowerCase().includes(query),
        ),
    );

    const effectiveLikes = (post: CommunityPost) =>
      post.likes + (likedIds.has(post.id) ? 1 : 0);

    const sorted = [...matched];
    if (order === "liked") {
      sorted.sort((a, b) => effectiveLikes(b) - effectiveLikes(a));
    } else {
      sorted.sort((a, b) => b.postedAt.localeCompare(a.postedAt));
    }
    return sorted;
  }, [search, order, likedIds]);

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
        sortBy={{ value: order, onChange: setOrder, options: sortOptions }}
      />

      {posts.length > 0 ? (
        <div className="space-y-5">
          {posts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              liked={likedIds.has(post.id)}
              onToggleLike={() => toggleLike(post.id)}
            />
          ))}
        </div>
      ) : (
        <p className="rounded-2xl border border-dashed border-border px-6 py-12 text-center text-sm text-text-muted">
          {searching
            ? `No stories match "${search.trim()}".`
            : "No stories yet."}
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
    <article className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-shadow hover:shadow-md">
      {post.image && (
        <div className="relative h-48 w-full sm:h-56">
          <Image
            src={post.image}
            alt={post.place}
            fill
            sizes="800px"
            className="object-cover"
          />
        </div>
      )}

      <div className="p-5 sm:p-6">
        <div className="flex items-center gap-3">
          <Avatar name={post.author} size="sm" />
          <div className="min-w-0">
            <p className="text-sm font-semibold">{post.author}</p>
            <p className="text-xs text-text-muted">
              {post.place} ·{" "}
              {dateFormatter.format(new Date(`${post.postedAt}T00:00:00Z`))}
            </p>
          </div>
        </div>

        <p className="mt-4 text-sm leading-relaxed text-text">
          {post.content}
        </p>

        <button
          type="button"
          onClick={onToggleLike}
          className={cn(
            "mt-4 inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
            liked ? "bg-danger/10 text-danger" : "text-text-muted hover:bg-bg",
          )}
        >
          <HeartIcon filled={liked} />
          {likeCount}
        </button>
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
