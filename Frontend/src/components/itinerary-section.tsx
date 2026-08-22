"use client";

import { Input, Select, controlStyles } from "@/components/ui/field";
import { cn } from "@/lib/cn";
import type { SelectOption } from "@/lib/types";

export type ItinerarySectionData = {
  id: string;
  cityId: string;
  description: string;
  startDate: string;
  endDate: string;
  budget: string;
};

type ItinerarySectionProps = {
  index: number;
  section: ItinerarySectionData;
  cities: SelectOption[];
  minDate?: string;
  maxDate?: string;
  error?: string;
  onChange: (patch: Partial<ItinerarySectionData>) => void;
  onRemove: () => void;
  removable: boolean;
};

export function ItinerarySection({
  index,
  section,
  cities,
  minDate,
  maxDate,
  error,
  onChange,
  onRemove,
  removable,
}: ItinerarySectionProps) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm transition-shadow hover:shadow-md sm:p-6">
      <div className="mb-4 flex items-center justify-between">
        <span className="inline-flex items-center gap-2 font-heading text-base font-semibold">
          <span className="flex size-7 items-center justify-center rounded-full bg-primary text-sm text-white">
            {index + 1}
          </span>
          Section {index + 1}
        </span>

        {removable && (
          <button
            type="button"
            onClick={onRemove}
            className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-medium text-text-muted transition-colors hover:bg-danger/10 hover:text-danger"
          >
            <TrashIcon />
            Remove
          </button>
        )}
      </div>

      {error && (
        <p className="mb-4 rounded-xl border border-danger/25 bg-danger/8 px-3.5 py-2.5 text-sm text-danger">
          {error}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Select
          label="City"
          placeholder="Which city is this section in?"
          options={cities}
          value={section.cityId}
          onChange={(event) => onChange({ cityId: event.target.value })}
          wrapperClassName="sm:col-span-2"
          required
        />

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
          min={minDate}
          max={maxDate}
          onChange={(event) => onChange({ startDate: event.target.value })}
          required
        />
        <Input
          label="End date"
          type="date"
          value={section.endDate}
          min={section.startDate || minDate}
          max={maxDate}
          onChange={(event) => onChange({ endDate: event.target.value })}
          required
        />

        <div className="space-y-1.5 sm:col-span-2">
          <label className="block text-sm font-medium text-text">
            Budget for this section
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-sm text-text-muted">
              ₹
            </span>
            <input
              type="number"
              inputMode="decimal"
              min={0}
              placeholder="0"
              value={section.budget}
              onChange={(event) => onChange({ budget: event.target.value })}
              className={cn(controlStyles, "h-11 pl-7")}
              required
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function TrashIcon() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="size-3.5"
      aria-hidden
    >
      <path d="M4 5.5h12M7.5 5.5V4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.5M8.25 9v5M11.75 9v5M5.5 5.5 6 16a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l.5-10.5" />
    </svg>
  );
}
