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
      <aside className="hidden flex-col justify-between bg-primary p-10 text-white lg:flex">
        <Link href="/" className="flex items-center gap-2">
          <GlobeMark />
          <span className="font-heading text-xl font-semibold">
            GlobeTrotter
          </span>
        </Link>

        <div className="max-w-sm">
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

        <p className="text-sm text-white/50">
          Odoo LDCE Hackathon 26 — GlobeTrotter
        </p>
      </aside>

      <main className="flex items-center justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-lg">{children}</div>
      </main>
    </div>
  );
}
