"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/field";
import { SectionHeader } from "@/components/section-header";
import { regions, suggestions } from "@/lib/mock-data";
import type { SelectOption } from "@/lib/types";

const placeOptions: SelectOption[] = regions.map((region) => ({
  label: `${region.name}, ${region.country}`,
  value: region.id,
}));

type Section = { id: string; label: string };

let sectionSeed = 0;
function nextSectionId() {
  sectionSeed += 1;
  return `section-${sectionSeed}`;
}

export function TripDetailsForm() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [added, setAdded] = useState<Set<string>>(new Set());
  const [sections, setSections] = useState<Section[]>([]);

  function toggleSuggestion(id: string, label: string) {
    setAdded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        setSections((current) => current.filter((section) => section.id !== id));
      } else {
        next.add(id);
        setSections((current) => [...current, { id, label }]);
      }
      return next;
    });
  }

  function addBlankSection() {
    setSections((current) => [
      ...current,
      { id: nextSectionId(), label: "" },
    ]);
  }

  function updateSectionLabel(id: string, label: string) {
    setSections((current) =>
      current.map((section) =>
        section.id === id ? { ...section, label } : section,
      ),
    );
  }

  function removeSection(id: string) {
    setSections((current) => current.filter((section) => section.id !== id));
    setAdded((prev) => {
      if (!prev.has(id)) return prev;
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    router.push("/trips/new/itinerary");
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-10">
      <div className="grid gap-4 rounded-2xl border border-border bg-surface p-6 shadow-sm sm:grid-cols-2 sm:p-8">
        <Input
          label="Trip title"
          placeholder="Kerala backwaters, take two"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          wrapperClassName="sm:col-span-2"
          required
        />

        <Select
          label="Select a place"
          placeholder="Choose a destination"
          options={placeOptions}
          value={placeId}
          onChange={(event) => setPlaceId(event.target.value)}
          wrapperClassName="sm:col-span-2"
          required
        />

        <Input
          label="Start date"
          type="date"
          value={startDate}
          onChange={(event) => setStartDate(event.target.value)}
          required
        />
        <Input
          label="End date"
          type="date"
          value={endDate}
          min={startDate || undefined}
          onChange={(event) => setEndDate(event.target.value)}
          required
        />
      </div>

      <section>
        <SectionHeader
          title="Suggestions for this trip"
          description="Tap to add places to visit or activities to perform — fine-tune each one in the next step."
        />
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion) => {
            const isAdded = added.has(suggestion.id);
            return (
              <button
                key={suggestion.id}
                type="button"
                onClick={() =>
                  toggleSuggestion(suggestion.id, suggestion.label)
                }
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-medium transition-all active:scale-[0.97]",
                  isAdded
                    ? "border-primary bg-primary text-white shadow-sm"
                    : "border-border bg-surface text-text hover:border-primary/30 hover:shadow-sm",
                )}
              >
                {isAdded && <CheckIcon />}
                {suggestion.label}
              </button>
            );
          })}
        </div>
      </section>

      <section>
        <SectionHeader
          title="Sections"
          description="Each section becomes a travel, stay or activity block in your itinerary."
        />

        {sections.length > 0 ? (
          <div className="space-y-3">
            {sections.map((section, index) => (
              <div
                key={section.id}
                className="flex items-center gap-3 rounded-xl border border-border bg-surface p-3 shadow-sm transition-shadow hover:shadow-md"
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                  {index + 1}
                </span>
                <input
                  value={section.label}
                  onChange={(event) =>
                    updateSectionLabel(section.id, event.target.value)
                  }
                  placeholder="Section name — hotel, travel, activity…"
                  className="min-w-0 flex-1 bg-transparent text-sm text-text outline-none placeholder:text-text-muted/70"
                />
                <button
                  type="button"
                  onClick={() => removeSection(section.id)}
                  aria-label="Remove section"
                  className="flex size-7 shrink-0 items-center justify-center rounded-full text-text-muted transition-colors hover:bg-danger/10 hover:text-danger"
                >
                  <CloseIcon />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="rounded-xl border border-dashed border-border px-4 py-6 text-center text-sm text-text-muted">
            No sections yet — add a suggestion above or start one from
            scratch.
          </p>
        )}

        <Button
          type="button"
          variant="outline"
          className="mt-4"
          onClick={addBlankSection}
        >
          <PlusIcon />
          Add another section
        </Button>
      </section>

      <div className="flex justify-end gap-3 border-t border-border pt-6">
        <Button type="submit" size="lg">
          Continue to itinerary
        </Button>
      </div>
    </form>
  );
}

function CloseIcon() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      className="size-4"
      aria-hidden
    >
      <path d="m5 5 10 10M15 5 5 15" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="size-3.5"
      aria-hidden
    >
      <path d="M3 8.5 6 11.5 13 4.5" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      className="size-4"
      aria-hidden
    >
      <path d="M8 3v10M3 8h10" />
    </svg>
  );
}
