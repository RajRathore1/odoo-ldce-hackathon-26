"use client";

import { Button } from "@/components/ui/button";

export default function MainError({ reset }: { reset: () => void }) {
  return (
    <div className="rounded-2xl border border-border bg-surface px-6 py-16 text-center">
      <h1 className="font-heading text-2xl font-semibold">
        That didn&apos;t load
      </h1>
      <p className="mx-auto mt-2 max-w-sm text-text-muted">
        The server didn&apos;t answer in time. It is usually back within a few
        seconds.
      </p>
      <Button className="mt-6" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}
