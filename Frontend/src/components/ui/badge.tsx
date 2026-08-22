import { cn } from "@/lib/cn";
import type { TripStatus } from "@/lib/types";

type Tone = "neutral" | "success" | "warning" | "info" | "danger" | "accent";

const dots: Record<Tone, string> = {
  neutral: "bg-text-muted",
  success: "bg-success",
  warning: "bg-warning",
  info: "bg-info",
  danger: "bg-danger",
  accent: "bg-accent",
};

const tints: Record<Tone, string> = {
  neutral: "bg-bg",
  success: "bg-success/12",
  warning: "bg-warning/15",
  info: "bg-info/12",
  danger: "bg-danger/12",
  accent: "bg-accent/15",
};

type BadgeProps = {
  tone?: Tone;
  children: React.ReactNode;
  className?: string;
};

export function Badge({ tone = "neutral", children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium text-text",
        tints[tone],
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", dots[tone])} />
      {children}
    </span>
  );
}

const statusTone: Record<TripStatus, Tone> = {
  ongoing: "warning",
  upcoming: "info",
  completed: "success",
};

const statusLabel: Record<TripStatus, string> = {
  ongoing: "Ongoing",
  upcoming: "Up-coming",
  completed: "Completed",
};

export function StatusBadge({
  status,
  className,
}: {
  status: TripStatus;
  className?: string;
}) {
  return (
    <Badge tone={statusTone[status]} className={className}>
      {statusLabel[status]}
    </Badge>
  );
}
