import Link from "next/link";
import { GlobeMark } from "@/components/navbar";

const highlights = [
  "Plan a trip in a few clicks",
  "Build a day-by-day itinerary",
  "Watch the budget as you go",
];

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="grid flex-1 lg:grid-cols-[1fr_1.1fr]">
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-primary p-10 text-white lg:flex">
        <div
          aria-hidden
          className="absolute -top-24 -right-24 size-96 rounded-full bg-accent/25 blur-3xl"
        />
        <div
          aria-hidden
          className="absolute bottom-0 left-0 h-72 w-72 -translate-x-1/3 translate-y-1/3 rounded-full bg-white/5 blur-3xl"
        />

        <Link href="/" className="relative z-10 flex items-center gap-2">
          <GlobeMark />
          <span className="font-heading text-xl font-semibold">
            GlobeTrotter
          </span>
        </Link>

        <div className="relative z-10 max-w-sm">
          <h1 className="font-heading text-3xl leading-tight font-semibold">
            Every great trip starts with a rough plan.
          </h1>
          <ul className="mt-8 space-y-4">
            {highlights.map((item) => (
              <li key={item} className="flex items-center gap-3 text-white/80">
                <span className="size-1.5 rounded-full bg-accent" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative z-10 text-sm text-white/50">
          Odoo LDCE Hackathon 26, GlobeTrotter
        </p>
      </aside>

      <main className="flex items-center justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-lg">{children}</div>
      </main>
    </div>
  );
}
