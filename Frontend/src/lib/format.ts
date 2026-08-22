const money = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const day = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short" });
const dayWithYear = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

export function formatMoney(amount: number) {
  return money.format(amount);
}

export function formatDateRange(start: string, end: string) {
  const from = new Date(start);
  const to = new Date(end);

  if (from.getFullYear() === to.getFullYear()) {
    return `${day.format(from)} – ${dayWithYear.format(to)}`;
  }

  return `${dayWithYear.format(from)} – ${dayWithYear.format(to)}`;
}

export function nightsBetween(start: string, end: string) {
  const ms = new Date(end).getTime() - new Date(start).getTime();
  return Math.max(0, Math.round(ms / 86_400_000));
}
