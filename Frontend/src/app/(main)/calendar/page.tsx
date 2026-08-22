import { CalendarView } from "@/components/calendar-view";

export default function CalendarPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Calendar
        </h1>
        <p className="mt-2 text-text-muted">
          See where your trips land across the month.
        </p>
      </div>

      <CalendarView />
    </div>
  );
}
