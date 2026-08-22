"use client";

import { cn } from "@/lib/cn";
import { controlStyles } from "@/components/ui/field";
import type { SelectOption } from "@/lib/types";

type DropdownConfig = {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
};

type SearchFilterBarProps = {
  search: string;
  onSearchChange: (value: string) => void;
  placeholder?: string;
  groupBy?: DropdownConfig;
  filter?: DropdownConfig;
  sortBy?: DropdownConfig;
  className?: string;
};

export function SearchFilterBar({
  search,
  onSearchChange,
  placeholder = "Search",
  groupBy,
  filter,
  sortBy,
  className,
}: SearchFilterBarProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-xl border border-border bg-surface p-3 sm:flex-row sm:items-center",
        className,
      )}
    >
      <div className="relative flex-1">
        <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-text-muted" />
        <input
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={placeholder}
          aria-label={placeholder}
          className={cn(controlStyles, "h-11 pl-9")}
        />
      </div>

      <div className="grid grid-cols-1 gap-3 sm:flex sm:items-center">
        <Dropdown label="Group by" dropdown={groupBy} />
        <Dropdown label="Filter" dropdown={filter} />
        <Dropdown label="Sort by" dropdown={sortBy} />
      </div>
    </div>
  );
}

function Dropdown({
  label,
  dropdown,
}: {
  label: string;
  dropdown?: DropdownConfig;
}) {
  if (!dropdown) return null;

  return (
    <select
      value={dropdown.value}
      onChange={(event) => dropdown.onChange(event.target.value)}
      aria-label={label}
      className={cn(controlStyles, "h-11 cursor-pointer sm:w-40")}
    >
      {dropdown.options.map((option) => (
        <option key={option.value} value={option.value}>
          {label}: {option.label}
        </option>
      ))}
    </select>
  );
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      className={className}
      aria-hidden
    >
      <circle cx="9" cy="9" r="6" />
      <path d="m13.5 13.5 3.5 3.5" />
    </svg>
  );
}
