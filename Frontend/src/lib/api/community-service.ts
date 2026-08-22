export type CursorPaginated<T> = {
  results: T[];
  pagination: {
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
    next: string | null;
    previous: string | null;
  };
};

export type PostAuthor = { first_name: string; avatar: string | null };

export type PostDto = {
  id: number;
  title: string;
  body: string;
  cover_image: string | null;
  author: PostAuthor;
  city: {
    id: number;
    name: string;
    state: string;
    country_name: string;
    image_url: string;
  } | null;
  trip: { id: number; name: string } | null;
  activity_name: string | null;
  likes_count: number;
  comments_count: number;
  is_liked_by_me: boolean;
  created_at: string;
};

export type CommentDto = {
  id: number;
  post: number;
  author: PostAuthor;
  parent: number | null;
  body: string;
  replies: CommentDto[];
  created_at: string;
};

export type CreatePostPayload = {
  title: string;
  body: string;
  city?: number | null;
  trip?: number | null;
};
