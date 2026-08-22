"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  ItinerarySection,
  type ItinerarySectionData,
} from "@/components/itinerary-section";
import { formatMoney } from "@/lib/format";

let sectionSeed = 0;
function nextSectionId() {
  sectionSeed += 1;
  return `itinerary-section-${sectionSeed}`;
}

function createEmptySection(): ItinerarySectionData {
  return {
    id: nextSectionId(),
    description: "",
    startDate: "",
    endDate: "",
    budget: "",
  };
}

export default function ItineraryBuilderPage() {
  const router = useRouter();
  const [sections, setSections] = useState<ItinerarySectionData[]>([
    createEmptySection(),
  ]);

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

  function handleSave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    router.push("/trips");
  }

  return (
    <form onSubmit={handleSave} className="space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Build your itinerary
        </h1>
        <p className="mt-2 max-w-xl text-text-muted">
          Break the trip into sections, like travel, stays, or activities,
          each with its own dates and budget.
        </p>
      </div>

      <div className="space-y-4">
        {sections.map((section, index) => (
          <ItinerarySection
            key={section.id}
            index={index}
            section={section}
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
          {formatMoney(totalBudget)}
        </span>
      </div>

      <div className="flex justify-end gap-3 border-t border-border pt-6">
        <Button type="submit" size="lg">
          Save itinerary
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
