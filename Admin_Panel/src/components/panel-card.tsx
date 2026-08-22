export function PanelCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6">
      <h2 className="font-heading text-lg font-semibold sm:text-xl">
        {title}
      </h2>
      {description && (
        <p className="mt-1 text-sm text-text-muted">{description}</p>
      )}
      <div className="mt-5">{children}</div>
    </div>
  );
}
