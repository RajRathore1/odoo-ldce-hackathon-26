"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { postJson } from "@/lib/api/browser";

type SaveDestinationButtonProps = {
  cityId: number;
  savedId: number | null;
};

export function SaveDestinationButton({
  cityId,
  savedId,
}: SaveDestinationButtonProps) {
  const router = useRouter();
  const [saved, setSaved] = useState<number | null>(savedId);
  const [busy, setBusy] = useState(false);

  async function toggle() {
    setBusy(true);

    try {
      if (saved === null) {
        const { saved: row } = await postJson<{ saved: { id: number } }>(
          "/api/saved-destinations",
          { city: cityId },
        );
        setSaved(row.id);
      } else {
        await fetch(`/api/saved-destinations/${saved}`, { method: "DELETE" });
        setSaved(null);
      }
      router.refresh();
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
