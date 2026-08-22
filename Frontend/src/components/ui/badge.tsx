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
  neutral: "bg-subtle",
  success: "bg-success/12",
  warning: "bg-warning/15",
  info: "bg-info/12",
  danger: "bg-danger/12",
  accent: "bg-accent/15",
};

const textTones: Record<Tone, string> = {
  neutral: "text-text-muted",
  success: "text-success",
  warning: "text-warning",
  info: "text-info",
  danger: "text-danger",
  accent: "text-accent",
};

type BadgeProps = {
  tone?: Tone;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

export function Badge({
  tone = "neutral",
  icon,
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium text-text",
        tints[tone],
        className,
      )}
    >
      {icon ? (
        <span className={cn("size-3", textTones[tone])}>{icon}</span>
      ) : (
        <span className={cn("size-1.5 rounded-full", dots[tone])} />
      )}
      {children}
    </span>
  );
}

const statusTone: Record<TripStatus, Tone> = {
  ongoing: "warning",
  upcoming: "info",
  completed: "success",
  cancelled: "danger",
};

const statusLabel: Record<TripStatus, string> = {
  ongoing: "Ongoing",
  upcoming: "Upcoming",
  completed: "Completed",
  cancelled: "Cancelled",
};

const statusIcon: Record<TripStatus, React.ReactNode> = {
  ongoing: (
    <svg
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <circle cx="6" cy="6" r="4.5" />
      <path d="M6 3.5V6l1.8 1.2" />
    </svg>
  ),
  upcoming: (
    <svg
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <rect x="1.5" y="2.5" width="9" height="8" rx="1.2" />
      <path d="M1.5 5h9M4 1.5v2M8 1.5v2" />
    </svg>
  ),
  completed: (
    <svg
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M2.5 6.3 5 8.8l4.5-5.6" />
    </svg>
  ),
  cancelled: (
    <svg
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <circle cx="6" cy="6" r="4.5" />
      <path d="M4 4l4 4" />
    </svg>
  ),
};

export function StatusBadge({
  status,
  className,
}: {
  status: TripStatus;
  className?: string;
}) {
  return (
    <Badge tone={statusTone[status]} icon={statusIcon[status]} className={className}>
      {statusLabel[status]}
    </Badge>
  );
}
