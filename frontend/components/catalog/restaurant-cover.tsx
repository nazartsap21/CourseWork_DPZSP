import Image from "next/image";

// Full class strings so Tailwind can see them at build time.
const FALLBACK_TONES = [
  "bg-accent text-white",
  "bg-sage text-white",
  "bg-saffron text-ink",
  "bg-clay text-white",
  "bg-accent-strong text-white",
  "bg-muted text-ink",
];

/** Restaurant photo, or a colored block with the initial when there's no image. */
export function RestaurantCover({
  id,
  name,
  imageUrl,
  label,
  className = "",
  initialClassName = "text-7xl",
}: {
  id: number;
  name: string;
  imageUrl: string | null;
  label?: string;
  className?: string;
  initialClassName?: string;
}) {
  if (imageUrl) {
    return (
      <div className={`relative overflow-hidden bg-surface ${className}`}>
        {/* Seed/admin URLs point to arbitrary hosts, so skip the optimizer. */}
        <Image src={imageUrl} alt={name} fill unoptimized className="object-cover" />
      </div>
    );
  }

  const tone = FALLBACK_TONES[id % FALLBACK_TONES.length];
  return (
    <div aria-hidden className={`relative overflow-hidden ${tone} ${className}`}>
      {label && (
        <span className="absolute right-4 top-3 text-[0.7rem] font-medium uppercase tracking-[0.2em] opacity-80">
          {label}
        </span>
      )}
      <span className={`absolute -bottom-[0.18em] left-4 font-serif leading-none ${initialClassName}`}>
        {name.charAt(0)}
      </span>
    </div>
  );
}
