import Image from "next/image";
import Link from "next/link";
import { LandingExplorer } from "@/components/landing-explorer";
import { GlobeMark } from "@/components/navbar";
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
          className="object-cover [filter:saturate(1.25)_contrast(1.08)_brightness(0.95)]"
        />
        <div
          aria-hidden
          className="absolute inset-0 bg-gradient-to-r from-primary/95 via-primary/70 to-primary/10"
        />
        <div
          aria-hidden
          className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-black/10"
        />
        <div
          aria-hidden
          className="absolute -top-24 -right-10 size-96 rounded-full bg-accent/30 blur-3xl mix-blend-screen"
        />
        <div
          aria-hidden
          className="absolute right-0 bottom-0 h-64 w-80 translate-x-1/4 translate-y-1/4 rounded-full bg-warning/20 blur-3xl mix-blend-screen"
        />

        <div className="relative max-w-2xl">
          <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur-sm">
            <GlobeMark className="size-3.5 text-accent" />
            GlobeTrotter
          </p>

          <h1 className="mt-5 font-heading text-4xl leading-[1.1] font-semibold sm:text-6xl">
            Somewhere new is closer than you think.
          </h1>

          <p className="mt-5 max-w-lg text-white/70">
            Sketch the route, block out the dates, and watch the budget add up
            as you go, all before you book a thing.
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
