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
