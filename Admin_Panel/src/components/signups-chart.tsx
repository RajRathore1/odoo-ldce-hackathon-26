export function SignupsChart({
  data,
}: {
  data: { month: string; users: number }[];
}) {
  const max = Math.max(...data.map((point) => point.users), 1);

  return (
    <div className="flex h-48 items-end gap-3 overflow-x-auto">
      {data.map((point) => (
        <div
          key={point.month}
          className="flex min-w-8 flex-1 flex-col items-center gap-2"
        >
          <span className="text-xs font-semibold text-text-muted">
            {point.users.toLocaleString("en-IN")}
          </span>
          <div className="flex h-32 w-full items-end">
            <div
              title={`${point.users.toLocaleString("en-IN")} new users`}
              className="w-full rounded-t-lg bg-gradient-to-t from-primary to-primary/70 transition-all hover:from-accent hover:to-accent/80"
              style={{ height: `${(point.users / max) * 100}%` }}
            />
          </div>
          <span className="text-xs text-text-muted">{point.month}</span>
        </div>
      ))}
    </div>
  );
}
