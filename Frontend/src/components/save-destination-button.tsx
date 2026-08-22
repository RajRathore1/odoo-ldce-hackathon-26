"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";
import type { SavedDestinationDto } from "@/lib/api/geo-service";

type SaveDestinationButtonProps = {
  cityId: number;
  savedId: number | null;
};

export function SaveDestinationButton({
  cityId,
  savedId,
}: SaveDestinationButtonProps) {
  const [saved, setSaved] = useState<number | null>(savedId);
  const [busy, setBusy] = useState(false);

  async function toggle() {
    setBusy(true);

    try {
      if (saved === null) {
        const row = await api<SavedDestinationDto>(
          "/users/me/saved-destinations/",
          { method: "POST", body: { city: cityId } },
        );
        setSaved(row.id);
      } else {
        await api(`/users/me/saved-destinations/${saved}/`, {
          method: "DELETE",
        });
        setSaved(null);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <Button
      variant={saved === null ? "outline" : "primary"}
      onClick={toggle}
      disabled={busy}
    >
      <BookmarkIcon filled={saved !== null} />
      {saved === null ? "Save" : "Saved"}
    </Button>
  );
}

function BookmarkIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinejoin="round"
      className="size-4"
      aria-hidden
    >
      <path d="M4 2.5h8v11l-4-2.75L4 13.5z" />
    </svg>
  );
}
