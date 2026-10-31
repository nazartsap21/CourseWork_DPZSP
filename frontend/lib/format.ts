const KOPIYKY_PER_UAH = 100;
const amountFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

/** 14500 -> "145 ₴", 5185 -> "51.85 ₴". */
export function formatPrice(kopiyky: number): string {
  return `${amountFormat.format(kopiyky / KOPIYKY_PER_UAH)} ₴`;
}

export function formatDeliveryWindow(min: number, max: number): string {
  return `${min}–${max} min`;
}

export function formatRating(rating: number): string {
  return rating.toFixed(1);
}

export function pluralize(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

const relativeFormat = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
const RELATIVE_STEPS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["minute", 60],
  ["hour", 24],
  ["day", 7],
  ["week", 4.35],
  ["month", 12],
];

/** "just now", "5 minutes ago", "yesterday", ... */
export function formatRelativeTime(iso: string, now: number = Date.now()): string {
  let value = (new Date(iso).getTime() - now) / 60_000;
  if (Math.abs(value) < 1) return "just now";
  for (const [unit, size] of RELATIVE_STEPS) {
    if (Math.abs(value) < size) return relativeFormat.format(Math.round(value), unit);
    value /= size;
  }
  return relativeFormat.format(Math.round(value), "year");
}

/** Kopiyky → the plain number an admin types in a form ("145", "51.85"). */
export function kopiykyToInput(kopiyky: number): string {
  return kopiyky % 100 === 0 ? String(kopiyky / 100) : (kopiyky / 100).toFixed(2);
}

/** "145", "145.5", "145,50" → kopiyky; null if it isn't a valid amount. */
export function inputToKopiyky(value: string): number | null {
  const normalized = value.trim().replace(",", ".");
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) return null;
  return Math.round(Number(normalized) * 100);
}
