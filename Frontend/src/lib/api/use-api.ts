"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/envelope";

type Loaded<T> = { key: string; data?: T; error?: string };

/**
 * GET a path from the browser.
 *
 * The result is stored alongside the request it belongs to, so a response that
 * arrives after the path has changed is ignored and the caller sees "loading"
 * rather than the previous page's data.
 *
 * Pass `null` to hold off entirely.
 */
export function useApi<T>(path: string | null) {
  const [loaded, setLoaded] = useState<Loaded<T>>({ key: "" });
  const [attempt, setAttempt] = useState(0);
  const key = path === null ? "" : `${path}#${attempt}`;

  useEffect(() => {
    if (path === null) return;

    let active = true;

    api<T>(path)
      .then((data) => {
        if (active) setLoaded({ key, data });
      })
      .catch((error: unknown) => {
        if (!active) return;
        setLoaded({
          key,
          error:
            error instanceof ApiError
              ? error.message
              : "Could not reach the server.",
        });
      });

    return () => {
      active = false;
    };
  }, [path, key]);

  const settled = path !== null && loaded.key === key;

  return {
    data: settled ? loaded.data : undefined,
    error: settled ? loaded.error : undefined,
    loading: path !== null && !settled,
    reload: () => setAttempt((value) => value + 1),
  };
}
