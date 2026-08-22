"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { SearchFilterBar } from "@/components/search-filter-bar";
import { buttonStyles } from "@/components/ui/button";
import { formatMoney } from "@/lib/format";
import { regions } from "@/lib/mock-data";
import type { Region, SelectOption } from "@/lib/types";

const sortOptions: SelectOption[] = [
  { label: "Most popular", value: "popular" },
  { label: "Price: low to high", value: "price-asc" },
  { label: "Price: high to low", value: "price-desc" },
  { label: "Name", value: "name" },
];

export function ExploreView() {
  const searchParams = useSearchParams();
  const [search, setSearch] = useState(() => {
    const regionId = searchParams.get("region");
    return regions.find((region) => region.id === regionId)?.name ?? "";
  });
  const [country, setCountry] = useState("all");
  const [order, setOrder] = useState("popular");

  const countryOptions = useMemo<SelectOption[]>(() => {
    const unique = [...new Set(regions.map((region) => region.country))].sort();
    return [
      { label: "All countries", value: "all" },
      ...unique.map((name) => ({ label: name, value: name })),
    ];
  }, []);

  const results = useMemo(() => {
    const query = search.trim().toLowerCase();
    const matched = regions.filter((region) => {
      const inCountry = country === "all" || region.country === country;
      const matchesQuery =
        !query ||
        [region.name, region.country, region.blurb].some((field) =>
          field.toLowerCase().includes(query),
        );
      return inCountry && matchesQuery;
    });

    const sorted = [...matched];
    switch (order) {
      case "price-asc":
        return sorted.sort((a, b) => a.fromPrice - b.fromPrice);
      case "price-desc":
        return sorted.sort((a, b) => b.fromPrice - a.fromPrice);
      case "name":
        return sorted.sort((a, b) => a.name.localeCompare(b.name));
      default:
        return sorted.sort((a, b) => b.tripCount - a.tripCount);
    }
  }, [search, country, order]);

  const searching = search.trim().length > 0;

  return (
    <div className="space-y-8">
      <SearchFilterBar
        search={search}
        onSearchChange={setSearch}
        placeholder="Search a city, country or activity"
        filter={{ value: country, onChange: setCountry, options: countryOptions }}
        sortBy={{ value: order, onChange: setOrder, options: sortOptions }}
      />

      {results.length > 0 ? (
        <div className="space-y-3">
          {results.map((region) => (
            <ExploreResultRow key={region.id} region={region} />
          ))}
        </div>
      ) : (
        <p className="rounded-2xl border border-dashed border-border px-6 py-12 text-center text-sm text-text-muted">
          {searching
            ? `No places match "${search.trim()}".`
            : "No places match those filters yet."}
        </p>
      )}
    </div>
  );
}

function ExploreResultRow({ region }: { region: Region }) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border bg-surface p-4 shadow-sm transition-shadow hover:shadow-md sm:flex-row sm:items-center">
      <div className="relative h-32 w-full shrink-0 overflow-hidden rounded-xl sm:h-20 sm:w-28">
        <Image
          src={region.image}
          alt={region.name}
          fill
          sizes="112px"
          className="object-cover"
        />
      </div>

      <div className="min-w-0 flex-1">
        <h3 className="font-semibold">{region.name}</h3>
        <p className="mt-0.5 text-sm text-text-muted">
          {region.country} · {region.blurb}
        </p>
      </div>

      <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end sm:justify-center sm:gap-1 sm:text-right">
        <p className="text-sm text-text-muted">{region.tripCount} trips planned</p>
        <p className="text-sm font-semibold text-primary">
          {formatMoney(region.fromPrice)}{" "}
          <span className="font-normal text-text-muted">to start</span>
        </p>
      </div>

      <Link
        href={`/explore/${region.id}`}
        className={buttonStyles("outline", "sm", "shrink-0")}
      >
        View
      </Link>
    </div>
  );
}
