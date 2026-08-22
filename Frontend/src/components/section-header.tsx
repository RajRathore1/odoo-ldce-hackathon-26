import Link from "next/link";

type SectionHeaderProps = {
  title: string;
  description?: string;
  action?: { label: string; href: string };
};

export function SectionHeader({
  title,
  description,
  action,
}: SectionHeaderProps) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <div>
        <h2 className="font-heading text-xl font-semibold sm:text-2xl">
          {title}
        </h2>
        {description && (
          <p className="mt-1 text-sm text-text-muted">{description}</p>
        )}
      </div>

      {action && (
        <Link
          href={action.href}
          className="shrink-0 text-sm font-medium text-text underline underline-offset-4 hover:text-accent"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}
