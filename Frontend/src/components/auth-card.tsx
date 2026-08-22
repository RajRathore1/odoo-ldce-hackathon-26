import Link from "next/link";

type AuthCardProps = {
  title: string;
  subtitle: string;
  footer: {
    prompt: string;
    linkLabel: string;
    href: string;
  };
  children: React.ReactNode;
};

export function AuthCard({ title, subtitle, footer, children }: AuthCardProps) {
  return (
    <div className="rounded-3xl border border-border bg-surface p-6 shadow-xl shadow-text/5 sm:p-8">
      <h1 className="font-heading text-2xl font-semibold">{title}</h1>
      <p className="mt-1.5 text-sm text-text-muted">{subtitle}</p>

      <div className="mt-6">{children}</div>

      <p className="mt-6 text-center text-sm text-text-muted">
        {footer.prompt}{" "}
        <Link
          href={footer.href}
          className="font-medium text-primary underline-offset-4 hover:underline"
        >
          {footer.linkLabel}
        </Link>
      </p>
    </div>
  );
}
