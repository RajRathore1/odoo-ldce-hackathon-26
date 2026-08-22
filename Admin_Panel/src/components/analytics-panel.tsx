"use client";

import { useState } from "react";
import { PanelCard } from "@/components/panel-card";
import { SignupsChart } from "@/components/signups-chart";
import { cn } from "@/lib/cn";
import { signupsByPeriod } from "@/lib/mock-data";

type Period = "6m" | "12m";

const periods: { value: Period; label: string }[] = [
  { value: "6m", label: "6 months" },
  { value: "12m", label: "12 months" },
];

export function AnalyticsPanel() {
  const [period, setPeriod] = useState<Period>("6m");

  return (
    <PanelCard
      title="User trends & analytics"
      description="New sign-ups over time."
      action={
        <div className="inline-flex rounded-full border border-border bg-bg p-1 text-sm">
          {periods.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setPeriod(option.value)}
              className={cn(
                "rounded-full px-3 py-1 font-medium transition-colors",
                period === option.value
                  ? "bg-primary text-white"
                  : "text-text-muted hover:text-text",
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      }
    >
      <SignupsChart data={signupsByPeriod[period]} />
    </PanelCard>
  );
}
