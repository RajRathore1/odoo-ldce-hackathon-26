"use client";

import type { ComponentType } from "react";
import { TrendUpIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import { useCountUp } from "@/lib/use-count-up";

type Tone = "primary" | "accent" | "success" | "info" | "warning";

const toneClasses: Record<Tone, string> = {
  primary: "bg-primary/10 text-primary",
  accent: "bg-accent/12 text-accent",
  success: "bg-success/12 text-success",
  info: "bg-info/12 text-info",
  warning: "bg-warning/15 text-warning",
};

export function StatCard({
  label,
  value,
  format,
  trend,
  icon: Icon,
  tone = "primary",
  style,
}: {
  label: string;
  value: number;
  format?: (value: number) => string;
  trend?: string;
  icon: ComponentType<{ className?: string }>;
  tone?: Tone;
  style?: React.CSSProperties;
}) {
  const animated = useCountUp(value);
  const display = format ? format(animated) : animated.toLocaleString("en-IN");

  return (
    <div
      style={style}
      className="animate-fade-up rounded-2xl border border-border bg-surface p-5 shadow-sm transition-shadow hover:shadow-md sm:p-6"
    >
      <div className="flex items-center justify-between">
        <span
          className={cn(
            "flex size-10 items-center justify-center rounded-xl",
            toneClasses[tone],
          )}
        >
          <Icon className="size-5" />
        </span>
        {trend && (
          <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-1 text-xs font-medium text-success">
            <TrendUpIcon className="size-3" />
            {trend}
          </span>
        )}
      </div>
      <p className="mt-4 text-sm font-medium text-text-muted">{label}</p>
      <p className="mt-1 font-heading text-2xl font-semibold tabular-nums sm:text-3xl">
        {display}
      </p>
    </div>
  );
}
