"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/cn";
import { FormAlert } from "@/components/form-alert";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/field";
import { SectionHeader } from "@/components/section-header";
import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/envelope";
import type { Region, SelectOption } from "@/lib/types";

type Section = { id: string; label: string };
type Suggestion = { id: string; label: string };

let sectionSeed = 0;
function nextSectionId() {
  sectionSeed += 1;
  return `section-${sectionSeed}`;
}

export function TripDetailsForm({ cities }: { cities: Region[] }) {
  const router = useRouter();
  const placeOptions: SelectOption[] = cities.map((city) => ({
    label: `${city.name}, ${city.country}`,
    value: city.id,
  }));
  const [title, setTitle] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [added, setAdded] = useState<Set<string>>(new Set());
  const [sections, setSections] = useState<Section[]>([]);
  const [loaded, setLoaded] = useState<{ cityId: string; items: Suggestion[] }>(
    { cityId: "", items: [] },
  );
  const [alert, setAlert] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  // What people actually do in the selected city, straight from the catalog.
  // The city is stored alongside the results so a slow response for a city the
  // user has already moved on from is simply ignored.
  useEffect(() => {
    if (!placeId) return;

    let active = true;

    api<{ id: number; name: string }[]>(
      `/activities/popular/?city=${placeId}&limit=12`,
    )
      .then((rows) => {
        if (!active) return;
        setLoaded({
          cityId: placeId,
          items: rows.map((row) => ({ id: String(row.id), label: row.name })),
        });
      })
      .catch(() => {
        if (active) setLoaded({ cityId: placeId, items: [] });
      });

    return () => {
      active = false;
    };
  }, [placeId]);

  const suggestionsReady = Boolean(placeId) && loaded.cityId === placeId;
  const suggestions = suggestionsReady ? loaded.items : [];

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

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (endDate < startDate) {
      setErrors({ end_date: "End date cannot be before the start date" });
      return;
    }

    setAlert(null);
    setErrors({});
    setSaving(true);

    // The chosen city becomes the description here; it turns into a real stop
    // on the next screen, where each section carries its own city and dates.
    const place = cities.find((city) => city.id === placeId);

    try {
      const trip = await api<{ id: number }>("/trips/", {
        method: "POST",
        body: {
          name: title,
          start_date: startDate,
          end_date: endDate,
          description: place ? `Around ${place.name}, ${place.country}` : "",
        },
      });
      router.push(`/trips/new/itinerary?trip=${trip.id}`);
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
        setErrors(error.fields);
      } else {
        setAlert("Could not reach the server.");
      }
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-10">
      <FormAlert message={alert} />

      <div className="grid gap-4 rounded-2xl border border-border bg-surface p-6 shadow-sm sm:grid-cols-2 sm:p-8">
        <Input
          label="Trip title"
          placeholder="Kerala backwaters, take two"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          error={errors.name}
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
          error={errors.start_date}
          required
        />
        <Input
          label="End date"
          type="date"
          value={endDate}
          min={startDate || undefined}
          onChange={(event) => setEndDate(event.target.value)}
          error={errors.end_date}
          required
        />
      </div>

      <section>
        <SectionHeader
          title="Suggestions for this trip"
          description="Tap to add places to visit or activities to perform, then fine-tune each one in the next step."
        />

        {!placeId && (
          <p className="rounded-xl border border-dashed border-border px-4 py-6 text-center text-sm text-text-muted">
            Pick a place above and we&apos;ll show what people do there.
          </p>
        )}

        {placeId && !suggestionsReady && (
          <p className="text-sm text-text-muted">Loading suggestions...</p>
        )}

        {suggestionsReady && suggestions.length === 0 && (
          <p className="rounded-xl border border-dashed border-border px-4 py-6 text-center text-sm text-text-muted">
            Nothing listed for this city yet.
          </p>
        )}

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
                  placeholder="Section name, e.g. hotel, travel, activity"
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
            No sections yet, add a suggestion above or start one from
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
        <Button type="submit" size="lg" disabled={saving}>
          {saving ? "Creating trip..." : "Continue to itinerary"}
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
