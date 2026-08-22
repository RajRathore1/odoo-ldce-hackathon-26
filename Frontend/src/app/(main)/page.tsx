import Image from "next/image";
import Link from "next/link";
import { LandingExplorer } from "@/components/landing-explorer";
import { buttonStyles } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="space-y-12">
      <section className="relative overflow-hidden rounded-3xl bg-primary px-6 py-14 text-white sm:px-12 sm:py-20">
        <Image
          src="https://images.unsplash.com/photo-1482914988630-16b155655e15?fm=jpg&q=80&w=2400&auto=format&fit=crop"
          alt="Mountain range at golden hour"
          fill
          priority
          className="object-cover"
        />
        <div
          aria-hidden
          className="absolute inset-0 bg-gradient-to-r from-primary/95 via-primary/75 to-primary/30"
        />
        <div
          aria-hidden
          className="absolute -top-24 -right-16 size-96 rounded-full bg-accent/20 blur-3xl"
        />

        <div className="relative max-w-2xl">
          <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium">
            <span className="size-1.5 rounded-full bg-accent" />
            GlobeTrotter
          </p>

          <h1 className="mt-5 font-heading text-4xl leading-[1.1] font-semibold sm:text-6xl">
            Somewhere new is closer than you think.
          </h1>

          <p className="mt-5 max-w-lg text-white/70">
            Sketch the route, block out the dates, and watch the budget add up
            as you go — all before you book a thing.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/trips/new" className={buttonStyles("accent", "lg")}>
              Plan a trip
            </Link>
            <Link
              href="/trips"
              className={buttonStyles(
                "outline",
                "lg",
                "border-white/25 bg-transparent text-white hover:border-white/40 hover:bg-white/10",
              )}
            >
              My trips
            </Link>
          </div>
        </div>
      </section>

      <LandingExplorer />
    </div>
  );
}
