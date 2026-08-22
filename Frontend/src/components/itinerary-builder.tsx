"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FormAlert } from "@/components/form-alert";
import {
  ItinerarySection,
  type ItinerarySectionData,
} from "@/components/itinerary-section";
import { Button } from "@/components/ui/button";
import { SubmitError, postJson } from "@/lib/api/browser";
import { formatMoney } from "@/lib/format";
import type { SelectOption } from "@/lib/types";

let sectionSeed = 0;
function nextSectionId() {
  sectionSeed += 1;
  return `itinerary-section-${sectionSeed}`;
}

function createEmptySection(): ItinerarySectionData {
  return {
    id: nextSectionId(),
    cityId: "",
    description: "",
    startDate: "",
    endDate: "",
    budget: "",
  };
}

type ItineraryBuilderProps = {
  tripId: string;
  tripName: string;
  tripStart: string;
  tripEnd: string;
  currency: string;
  cities: SelectOption[];
};

export function ItineraryBuilder({
  tripId,
  tripName,
  tripStart,
  tripEnd,
  currency,
  cities,
}: ItineraryBuilderProps) {
  const router = useRouter();
  const [sections, setSections] = useState<ItinerarySectionData[]>([
    createEmptySection(),
  ]);
  const [alert, setAlert] = useState<string | null>(null);
  const [failedIndex, setFailedIndex] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const totalBudget = sections.reduce(
    (sum, section) => sum + (Number(section.budget) || 0),
    0,
  );

  function addSection() {
    setSections((current) => [...current, createEmptySection()]);
  }

  function updateSection(id: string, patch: Partial<ItinerarySectionData>) {
    setSections((current) =>
      current.map((section) =>
        section.id === id ? { ...section, ...patch } : section,
      ),
    );
  }

  function removeSection(id: string) {
    setSections((current) => current.filter((section) => section.id !== id));
  }

  async function handleSave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAlert(null);
    setFailedIndex(null);

    const outOfRange = sections.findIndex(
      (section) => section.startDate < tripStart || section.endDate > tripEnd,
    );
    if (outOfRange !== -1) {
      setFailedIndex(outOfRange);
      setAlert("Every section has to sit inside the trip's own dates.");
      return;
    }

    setSaving(true);

    try {
      await postJson(`/api/trips/${tripId}/stops`, {
        stops: sections.map((section) => ({
          city: Number(section.cityId),
          start_date: section.startDate,
          end_date: section.endDate,
          title: section.description,
          budget: section.budget || undefined,
        })),
      });
      router.push(`/trips/${tripId}`);
      router.refresh();
    } catch (error) {
      if (error instanceof SubmitError) setAlert(error.message);
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Build your itinerary
        </h1>
        <p className="mt-2 max-w-xl text-text-muted">
          Break {tripName} into sections, like travel, stays, or activities,
          each with its own city, dates and budget.
        </p>
      </div>

      <FormAlert message={alert} />

      <div className="space-y-4">
        {sections.map((section, index) => (
          <ItinerarySection
            key={section.id}
            index={index}
            section={section}
            cities={cities}
            minDate={tripStart}
            maxDate={tripEnd}
            error={
              failedIndex === index
                ? "These dates fall outside the trip."
                : undefined
            }
            onChange={(patch) => updateSection(section.id, patch)}
            onRemove={() => removeSection(section.id)}
            removable={sections.length > 1}
          />
        ))}
      </div>

      <Button type="button" variant="outline" onClick={addSection}>
        <PlusIcon />
        Add another section
      </Button>

      <div className="flex items-center justify-between rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6">
        <span className="font-medium text-text-muted">Total budget</span>
        <span className="font-heading text-xl font-semibold text-primary">
          {formatMoney(totalBudget, currency)}
        </span>
      </div>

      <div className="flex justify-end gap-3 border-t border-border pt-6">
        <Button type="submit" size="lg" disabled={saving}>
          {saving ? "Saving..." : "Save itinerary"}
        </Button>
      </div>
    </form>
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
