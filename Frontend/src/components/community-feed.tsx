"use client";

import Image from "next/image";
import { useMemo, useState } from "react";
import { FormAlert } from "@/components/form-alert";
import { ErrorBlock, LoadingBlock } from "@/components/page-state";
import { SearchFilterBar } from "@/components/search-filter-bar";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/field";
import { api } from "@/lib/api/client";
import type {
  CursorPaginated,
  PostDto,
} from "@/lib/api/community-service";
import { ApiError } from "@/lib/api/envelope";
import type { CityDto } from "@/lib/api/geo-service";
import type { Paginated } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";
import { cn } from "@/lib/cn";
import type { SelectOption } from "@/lib/types";

const sortOptions: SelectOption[] = [
  { label: "Newest", value: "-created_at" },
  { label: "Most liked", value: "-likes_count" },
];

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});

export function CommunityFeed() {
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("all");
  const [order, setOrder] = useState("-created_at");
  const [composing, setComposing] = useState(false);

  const query = new URLSearchParams({ ordering: order });
  if (search.trim()) query.set("search", search.trim());
  if (city !== "all") query.set("city", city);

  const feed = useApi<CursorPaginated<PostDto>>(`/community/posts/?${query}`);
  const cities = useApi<Paginated<CityDto>>("/cities/?page_size=100");

  const cityOptions = useMemo<SelectOption[]>(
    () => [
      { label: "All cities", value: "all" },
      ...(cities.data?.results ?? []).map((row) => ({
        label: `${row.name}, ${row.country.name}`,
        value: String(row.id),
      })),
    ],
    [cities.data],
  );

  const posts = feed.data?.results ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SearchFilterBar
          className="flex-1"
          search={search}
          onSearchChange={setSearch}
          placeholder="Search a place, traveller or story"
          filter={{ value: city, onChange: setCity, options: cityOptions }}
          sortBy={{ value: order, onChange: setOrder, options: sortOptions }}
        />
        <Button onClick={() => setComposing(!composing)}>
          {composing ? "Cancel" : "Share a story"}
        </Button>
      </div>

      {composing && (
        <PostComposer
          cities={cityOptions.slice(1)}
          onPosted={() => {
            setComposing(false);
            feed.reload();
          }}
        />
      )}

      {feed.loading && <LoadingBlock label="Loading stories" />}
      {feed.error && <ErrorBlock message={feed.error} onRetry={feed.reload} />}

      {feed.data && posts.length > 0 && (
        <div className="space-y-5">
          {posts.map((post, index) => (
            <div
              key={post.id}
              className="animate-fade-up"
              style={{ animationDelay: `${Math.min(index, 5) * 60}ms` }}
            >
              <PostCard post={post} />
            </div>
          ))}
        </div>
      )}

      {feed.data && posts.length === 0 && (
        <p className="rounded-2xl border border-dashed border-border px-6 py-12 text-center text-sm text-text-muted">
          {search.trim()
            ? `No stories match "${search.trim()}".`
            : "No stories yet. Be the first to share one."}
        </p>
      )}
    </div>
  );
}

function PostComposer({
  cities,
  onPosted,
}: {
  cities: SelectOption[];
  onPosted: () => void;
}) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [city, setCity] = useState("");
  const [alert, setAlert] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAlert(null);
    setSaving(true);

    try {
      await api("/community/posts/", {
        method: "POST",
        body: {
          title,
          body,
          city: city ? Number(city) : null,
        },
      });
      onPosted();
    } catch (error) {
      setAlert(
        error instanceof ApiError
          ? error.message
          : "Could not reach the server.",
      );
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="space-y-4 rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6"
    >
      <FormAlert message={alert} />

      <Input
        label="Title"
        placeholder="Bir Billing was unreal"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        required
      />
      <Textarea
        label="Your story"
        placeholder="What made it worth the trip?"
        value={body}
        onChange={(event) => setBody(event.target.value)}
        required
      />
      <Select
        label="City"
        options={cities}
        placeholder="Somewhere in particular?"
        value={city}
        onChange={(event) => setCity(event.target.value)}
      />

      <Button type="submit" disabled={saving}>
        {saving ? "Posting..." : "Post story"}
      </Button>
    </form>
  );
}

function PostCard({ post }: { post: PostDto }) {
  // Liking answers with the updated post, so the card owns its own copy from
  // then on rather than waiting for the whole feed to reload.
  const [state, setState] = useState({
    liked: post.is_liked_by_me,
    likes: post.likes_count,
  });
  const [busy, setBusy] = useState(false);

  const image = post.cover_image ?? post.city?.image_url ?? null;
  const place = post.city
    ? `${post.city.name}, ${post.city.country_name}`
    : "Somewhere out there";

  async function toggleLike() {
    setBusy(true);
    const next = !state.liked;

    try {
      const updated = await api<PostDto>(`/community/posts/${post.id}/like/`, {
        method: next ? "POST" : "DELETE",
        body: next ? {} : undefined,
      });
      setState({
        liked: updated?.is_liked_by_me ?? next,
        likes: updated?.likes_count ?? state.likes + (next ? 1 : -1),
      });
    } catch {
      // leave the card as it was
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="group overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
      {image && (
        <div className="relative h-56 w-full sm:h-64">
          <Image
            src={image}
            alt={place}
            fill
            sizes="800px"
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-black/10" />

          <button
            type="button"
            onClick={toggleLike}
            disabled={busy}
            aria-pressed={state.liked}
            aria-label={state.liked ? "Unlike this story" : "Like this story"}
            className={cn(
              "absolute top-3 right-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium shadow-sm backdrop-blur-sm transition-all active:scale-95",
              state.liked
                ? "bg-danger text-white"
                : "bg-white/90 text-text hover:bg-white",
            )}
          >
            <HeartIcon filled={state.liked} />
            {state.likes}
          </button>

          <div className="absolute inset-x-0 bottom-0 flex items-center gap-3 p-4 text-white">
            <Avatar
              name={post.author.first_name}
              src={post.author.avatar}
              size="sm"
              className="ring-2 ring-white/70"
            />
            <div className="min-w-0">
              <p className="text-sm font-semibold">{post.author.first_name}</p>
              <p className="text-xs text-white/80">
                {place} · {dateFormatter.format(new Date(post.created_at))}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="p-5 sm:p-6">
        <h3 className="font-heading text-lg font-semibold">{post.title}</h3>
        <p className="mt-2 text-sm leading-relaxed text-text">{post.body}</p>

        <div className="mt-4 flex items-center gap-4 border-t border-border pt-3 text-sm text-text-muted">
          {!image && (
            <button
              type="button"
              onClick={toggleLike}
              disabled={busy}
              aria-pressed={state.liked}
              className={cn(
                "inline-flex items-center gap-1.5 font-medium transition-colors",
                state.liked ? "text-danger" : "hover:text-text",
              )}
            >
              <HeartIcon filled={state.liked} />
              {state.likes}
            </button>
          )}
          <span>
            {post.comments_count}{" "}
            {post.comments_count === 1 ? "comment" : "comments"}
          </span>
        </div>
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
