"use client";

import type { ComponentType } from "react";
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
        "flex flex-col gap-3 rounded-2xl border border-border bg-surface p-3 shadow-sm transition-shadow hover:shadow-md sm:flex-row sm:items-center",
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
        <Dropdown label="Group by" dropdown={groupBy} icon={LayersIcon} />
        <Dropdown label="Filter" dropdown={filter} icon={FunnelIcon} />
        <Dropdown label="Sort by" dropdown={sortBy} icon={SortIcon} />
      </div>
    </div>
  );
}

function Dropdown({
  label,
  dropdown,
  icon: Icon,
}: {
  label: string;
  dropdown?: DropdownConfig;
  icon: ComponentType<{ className?: string }>;
}) {
  if (!dropdown) return null;

  return (
    <div className="relative">
      <Icon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-text-muted" />
      <select
        value={dropdown.value}
        onChange={(event) => dropdown.onChange(event.target.value)}
        aria-label={label}
        className={cn(controlStyles, "h-11 cursor-pointer pl-9 sm:w-44")}
      >
        {dropdown.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
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

function FunnelIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M3 4h14l-5.5 6.2V16l-3 1.5v-7.3L3 4Z" />
    </svg>
  );
}

function SortIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M6 4v12M6 4 3.5 6.5M6 4l2.5 2.5M14 16V4m0 12 2.5-2.5M14 16l-2.5-2.5" />
    </svg>
  );
}

function LayersIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="m10 3 7 3.5-7 3.5-7-3.5L10 3Z" />
      <path d="m3 10.5 7 3.5 7-3.5" />
    </svg>
  );
}
