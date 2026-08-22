export function SignupsChart({
  data,
}: {
  data: { month: string; users: number }[];
}) {
  const max = Math.max(...data.map((point) => point.users), 1);

  return (
    <div className="flex h-40 items-end gap-3">
      {data.map((point) => (
        <div
          key={point.month}
          className="flex flex-1 flex-col items-center gap-2"
        >
          <div className="flex h-32 w-full items-end">
            <div
              title={`${point.users.toLocaleString("en-IN")} new users`}
              className="w-full rounded-t-md bg-primary transition-all hover:bg-accent"
              style={{ height: `${(point.users / max) * 100}%` }}
            />
          </div>
          <span className="text-xs text-text-muted">{point.month}</span>
        </div>
      ))}
    </div>
  );
}
