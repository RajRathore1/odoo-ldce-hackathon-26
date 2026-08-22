import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/cn";
import { StatusBadge } from "@/components/ui/badge";
import { formatDateRange, formatMoney } from "@/lib/format";
import type { Trip } from "@/lib/types";

type TripCardProps = {
  trip: Trip;
  href?: string;
  className?: string;
};

export function TripCard({ trip, href, className }: TripCardProps) {
  const card = (
    <article
      className={cn(
        "group flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-surface transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg",
        className,
      )}
    >
      <div className="relative h-28 overflow-hidden bg-bg sm:h-32">
        <Image
          src={trip.image}
          alt={trip.title}
          fill
          sizes="(min-width: 1024px) 40vw, (min-width: 640px) 60vw, 100vw"
          className="object-cover transition-transform duration-300 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-black/0 to-black/10 transition-colors duration-200 group-hover:from-black/50" />
        <span className="absolute top-3 left-3 rounded-full bg-surface/90 px-2.5 py-1 text-xs font-medium text-primary shadow-sm backdrop-blur-sm">
          {trip.city}, {trip.country}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-base leading-snug font-semibold">{trip.title}</h3>
          <StatusBadge status={trip.status} />
        </div>

        <p className="text-sm text-text-muted">
          {formatDateRange(trip.startDate, trip.endDate)}
        </p>

        <div className="mt-auto flex items-center justify-between border-t border-border pt-3 text-sm">
          <span className="text-text-muted">
            {trip.stops} {trip.stops === 1 ? "stop" : "stops"}
          </span>
          <span className="font-semibold text-primary">
            {formatMoney(trip.budget)}
          </span>
        </div>
      </div>
    </article>
  );

  if (!href) return card;

  return (
    <Link href={href} className="block focus-visible:outline-none">
      {card}
    </Link>
  );
}
