import { TripsBrowser } from "@/components/trips-browser";
import { listTrips } from "@/lib/api/trips-service";

export default async function TripsPage() {
  const trips = await listTrips();
  return <TripsBrowser trips={trips} />;
}
