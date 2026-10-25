import { Star } from "lucide-react";

/** Read-only star row, e.g. ★★★★☆ for 4. */
export function Stars({ rating, size = "h-4 w-4" }: { rating: number; size?: string }) {
  return (
    <span className="inline-flex gap-0.5" role="img" aria-label={`${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((value) => (
        <Star
          key={value}
          aria-hidden
          className={`${size} ${value <= rating ? "fill-saffron text-saffron" : "text-line"}`}
        />
      ))}
    </span>
  );
}

const STAR_LABELS = ["Bad", "Not great", "Okay", "Good", "Excellent"];

/** Star picker as a radio group: keyboard and screen readers get proper choices. */
export function StarInput({ value, onChange }: { value: number; onChange: (rating: number) => void }) {
  return (
    <div role="radiogroup" aria-label="Rating" className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((rating) => (
        <button
          key={rating}
          type="button"
          role="radio"
          aria-checked={value === rating}
          aria-label={`${rating} – ${STAR_LABELS[rating - 1]}`}
          onClick={() => onChange(rating)}
          className="rounded p-0.5 transition hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          <Star aria-hidden className={`h-7 w-7 ${rating <= value ? "fill-saffron text-saffron" : "text-muted-ink/40"}`} />
        </button>
      ))}
      {value > 0 && <span className="ml-2 text-sm text-muted-ink">{STAR_LABELS[value - 1]}</span>}
    </div>
  );
}
