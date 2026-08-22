import { TripDetailsForm } from "@/components/trip-details-form";
import { listCities } from "@/lib/api/geo-service";

export default async function NewTripPage() {
  const cities = await listCities();

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Plan a new trip
        </h1>
        <p className="mt-2 max-w-xl text-text-muted">
          Pick a place, block out your dates, then start pulling in the
          things you don&apos;t want to miss.
        </p>
      </div>

      <TripDetailsForm cities={cities} />
    </div>
  );
}
