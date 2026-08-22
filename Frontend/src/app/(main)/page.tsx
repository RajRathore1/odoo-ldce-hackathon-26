import Link from "next/link";
import { buttonStyles } from "@/components/ui/button";

export default function HomePage() {
  return (
    <section className="rounded-2xl border border-border bg-surface p-8 sm:p-12">
      <p className="text-sm font-medium text-accent">You&apos;re signed in</p>
      <h1 className="mt-2 font-heading text-3xl font-semibold sm:text-4xl">
        Welcome to GlobeTrotter
      </h1>
      <p className="mt-3 max-w-xl text-text-muted">
        The landing page with regional picks and previous trips lands next. In
        the meantime, jump straight into planning.
      </p>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/trips/new" className={buttonStyles("accent")}>
          Plan a trip
        </Link>
        <Link href="/login" className={buttonStyles("outline")}>
          Back to login
        </Link>
      </div>
    </section>
  );
}
