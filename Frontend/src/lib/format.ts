// Cities are priced in their own currency, so keep a formatter per currency.
const moneyFormatters = new Map<string, Intl.NumberFormat>();

function moneyFormatter(currency: string) {
  let formatter = moneyFormatters.get(currency);
  if (!formatter) {
    formatter = new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    });
    moneyFormatters.set(currency, formatter);
  }
  return formatter;
}

// Trip dates are plain YYYY-MM-DD, so format them in UTC — otherwise the
// server and the browser can disagree by a day and hydration blows up.
const day = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});
const dayWithYear = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

export function formatMoney(amount: number, currency = "INR") {
  return moneyFormatter(currency).format(amount);
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
