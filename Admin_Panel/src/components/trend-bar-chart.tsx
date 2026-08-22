export function TrendBarChart({
  data,
}: {
  data: { label: string; users: number }[];
}) {
  const max = Math.max(...data.map((point) => point.users), 1);

  return (
    <div className="flex h-64 items-end gap-3 sm:gap-4">
      {data.map((point) => (
        <div
          key={point.label}
          className="flex min-w-0 flex-1 flex-col items-center gap-2"
        >
          <span className="text-xs font-semibold text-text-muted">
            {point.users.toLocaleString("en-IN")}
          </span>
          <div className="flex h-48 w-full items-end">
            <div
              title={`${point.users.toLocaleString("en-IN")} new users`}
              className="w-full rounded-t-lg bg-gradient-to-t from-primary to-primary/60 transition-all duration-500 ease-out hover:from-accent hover:to-accent/70"
              style={{ height: `${(point.users / max) * 100}%` }}
            />
          </div>
          <span className="text-xs text-text-muted">{point.label}</span>
        </div>
      ))}
    </div>
  );
}
