"use client";

import { useId } from "react";
import { cn } from "@/lib/cn";
import type { SelectOption } from "@/lib/types";

export const controlStyles =
  "w-full rounded-xl border border-border bg-surface px-3 text-sm text-text transition-all placeholder:text-text-muted/70 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15 disabled:bg-subtle";

const errorStyles = "border-danger focus:border-danger focus:ring-danger/20";

type FieldShellProps = {
  id: string;
  label?: string;
  hint?: string;
  error?: string;
  className?: string;
  children: React.ReactNode;
};

function FieldShell({
  id,
  label,
  hint,
  error,
  className,
  children,
}: FieldShellProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-text">
          {label}
        </label>
      )}
      {children}
      {error ? (
        <p className="text-xs text-danger">{error}</p>
      ) : (
        hint && <p className="text-xs text-text-muted">{hint}</p>
      )}
    </div>
  );
}

type InputProps = Omit<React.ComponentProps<"input">, "size"> & {
  label?: string;
  hint?: string;
  error?: string;
  wrapperClassName?: string;
};

export function Input({
  label,
  hint,
  error,
  id,
  className,
  wrapperClassName,
  ...props
}: InputProps) {
  const fallbackId = useId();
  const fieldId = id ?? fallbackId;

  return (
    <FieldShell
      id={fieldId}
      label={label}
      hint={hint}
      error={error}
      className={wrapperClassName}
    >
      <input
        id={fieldId}
        className={cn(controlStyles, "h-11", error && errorStyles, className)}
        {...props}
      />
    </FieldShell>
  );
}

type TextareaProps = React.ComponentProps<"textarea"> & {
  label?: string;
  hint?: string;
  error?: string;
  wrapperClassName?: string;
};

export function Textarea({
  label,
  hint,
  error,
  id,
  className,
  wrapperClassName,
  rows = 4,
  ...props
}: TextareaProps) {
  const fallbackId = useId();
  const fieldId = id ?? fallbackId;

  return (
    <FieldShell
      id={fieldId}
      label={label}
      hint={hint}
      error={error}
      className={wrapperClassName}
    >
      <textarea
        id={fieldId}
        rows={rows}
        className={cn(
          controlStyles,
          "resize-y py-2.5 leading-relaxed",
          error && errorStyles,
          className,
        )}
        {...props}
      />
    </FieldShell>
  );
}

type SelectProps = React.ComponentProps<"select"> & {
  label?: string;
  hint?: string;
  error?: string;
  options: SelectOption[];
  placeholder?: string;
  wrapperClassName?: string;
};

export function Select({
  label,
  hint,
  error,
  options,
  placeholder,
  id,
  className,
  wrapperClassName,
  ...props
}: SelectProps) {
  const fallbackId = useId();
  const fieldId = id ?? fallbackId;

  return (
    <FieldShell
      id={fieldId}
      label={label}
      hint={hint}
      error={error}
      className={wrapperClassName}
    >
      <select
        id={fieldId}
        className={cn(
          controlStyles,
          "h-11 cursor-pointer appearance-none pr-8",
          error && errorStyles,
          className,
        )}
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8' fill='none' stroke='%235C6570' stroke-width='1.6'%3E%3Cpath d='M1 1.5 6 6.5 11 1.5'/%3E%3C/svg%3E\")",
          backgroundRepeat: "no-repeat",
          backgroundPosition: "right 0.75rem center",
          backgroundSize: "0.7rem",
        }}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </FieldShell>
  );
}
