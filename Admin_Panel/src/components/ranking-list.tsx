import { cn } from "@/lib/cn";

export function RankingList({
  items,
}: {
  items: { label: string; sublabel?: string; value: number }[];
}) {
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <ul className="space-y-4">
      {items.map((item, index) => {
        const intensity = Math.max(item.value / max, 0.25);

        return (
          <li key={item.label} className="flex items-center gap-3">
            <span
              className={cn(
                "flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                index === 0
                  ? "bg-accent text-white"
                  : "bg-primary/10 text-primary",
              )}
            >
              {index + 1}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-3">
                <p
                  className={cn(
                    "truncate text-sm",
                    index === 0 ? "font-semibold" : "font-medium",
                  )}
                >
                  {item.label}
                </p>
                <p className="shrink-0 text-sm font-semibold text-text-muted">
                  {item.value.toLocaleString("en-IN")}
                </p>
              </div>
              {item.sublabel && (
                <p className="text-xs text-text-muted">{item.sublabel}</p>
              )}
              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-subtle">
                <div
                  className="h-full rounded-full bg-accent transition-[width,opacity] duration-500 ease-out"
                  style={{
                    width: `${(item.value / max) * 100}%`,
                    opacity: intensity,
                  }}
                />
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
