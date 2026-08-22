import Link from "next/link";
import { buttonStyles } from "@/components/ui/button";

export default function HomePage() {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-border bg-surface p-8 sm:p-12">
      <div
        aria-hidden
        className="absolute -top-20 -right-20 size-72 rounded-full bg-accent/15 blur-3xl"
      />

      <p className="relative inline-flex items-center gap-1.5 text-sm font-medium text-accent">
        <span className="size-1.5 rounded-full bg-accent" />
        You&apos;re signed in
      </p>
      <h1 className="relative mt-3 max-w-2xl font-heading text-3xl font-semibold tracking-tight sm:text-5xl">
        Welcome to GlobeTrotter
      </h1>
      <p className="relative mt-4 max-w-xl text-text-muted">
        The landing page with regional picks and previous trips lands next. In
        the meantime, jump straight into planning.
      </p>

      <div className="relative mt-8 flex flex-wrap gap-3">
        <Link href="/trips/new" className={buttonStyles("accent", "lg")}>
          Plan a trip
        </Link>
        <Link href="/login" className={buttonStyles("outline", "lg")}>
          Back to login
        </Link>
      </div>
    </section>
  );
}
