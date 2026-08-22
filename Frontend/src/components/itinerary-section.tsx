"use client";

import { Input } from "@/components/ui/field";

export type ItinerarySectionData = {
  id: string;
  description: string;
  startDate: string;
  endDate: string;
  budget: string;
};

type ItinerarySectionProps = {
  index: number;
  section: ItinerarySectionData;
  onChange: (patch: Partial<ItinerarySectionData>) => void;
  onRemove: () => void;
  removable: boolean;
};

export function ItinerarySection({
  index,
  section,
  onChange,
  onRemove,
  removable,
}: ItinerarySectionProps) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6">
      <div className="mb-4 flex items-center justify-between">
        <span className="inline-flex items-center gap-2 font-heading text-base font-semibold">
          <span className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-sm text-primary">
            {index + 1}
          </span>
          Section {index + 1}
        </span>

        {removable && (
          <button
            type="button"
            onClick={onRemove}
            className="text-sm font-medium text-text-muted hover:text-danger"
          >
            Remove
          </button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Section description"
          placeholder="Travel section, hotel, or any other activity"
          value={section.description}
          onChange={(event) => onChange({ description: event.target.value })}
          wrapperClassName="sm:col-span-2"
          required
        />

        <Input
          label="Start date"
          type="date"
          value={section.startDate}
          onChange={(event) => onChange({ startDate: event.target.value })}
          required
        />
        <Input
          label="End date"
          type="date"
          value={section.endDate}
          min={section.startDate || undefined}
          onChange={(event) => onChange({ endDate: event.target.value })}
          required
        />

        <Input
          label="Budget for this section"
          type="number"
          inputMode="decimal"
          min={0}
          placeholder="0"
          value={section.budget}
          onChange={(event) => onChange({ budget: event.target.value })}
          wrapperClassName="sm:col-span-2"
          required
        />
      </div>
    </div>
  );
}
