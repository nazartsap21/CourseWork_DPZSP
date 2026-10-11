import { formatPrice } from "@/lib/format";
import type { Dish, Menu } from "@/types/catalog";

function sectionId(category: string): string {
  return `menu-${category.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}

function DishRow({ dish }: { dish: Dish }) {
  return (
    <li
      className={`flex items-start justify-between gap-4 border-b border-line py-4 ${
        dish.is_available ? "" : "opacity-55"
      }`}
    >
      <div className="min-w-0">
        <h3 className="font-medium text-ink">{dish.name}</h3>
        {dish.description && <p className="mt-1 text-sm leading-relaxed text-muted-ink">{dish.description}</p>}
      </div>
      <div className="shrink-0 text-right">
        <p className="font-medium tabular-nums text-ink">{formatPrice(dish.price)}</p>
        {!dish.is_available && <p className="mt-1 text-xs uppercase tracking-wider text-accent-strong">Sold out</p>}
      </div>
    </li>
  );
}

export function MenuSections({ menu }: { menu: Menu }) {
  if (menu.sections.length === 0) {
    return <p className="text-muted-ink">The menu is being updated. Check back soon.</p>;
  }

  return (
    <>
      {/* Category bar stays visible while scrolling a long menu. */}
      <nav
        aria-label="Menu categories"
        className="sticky top-0 z-10 -mx-4 overflow-x-auto border-b border-line bg-background px-4 sm:mx-0 sm:px-0"
      >
        <ul className="flex gap-6 whitespace-nowrap py-3 text-sm">
          {menu.sections.map((section) => (
            <li key={section.category}>
              <a href={`#${sectionId(section.category)}`} className="font-medium text-muted-ink hover:text-accent-strong">
                {section.category}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <div className="mt-4 space-y-10">
        {menu.sections.map((section) => (
          <section key={section.category} id={sectionId(section.category)} className="scroll-mt-16">
            <h2 className="font-serif text-2xl text-ink">
              {section.category}
              <span className="ml-2 align-middle text-sm font-normal text-muted-ink">{section.dishes.length}</span>
            </h2>
            <ul className="grid gap-x-10 md:grid-cols-2">
              {section.dishes.map((dish) => (
                <DishRow key={dish.id} dish={dish} />
              ))}
            </ul>
          </section>
        ))}
      </div>
    </>
  );
}

export function MenuSkeleton() {
  return (
    <div aria-hidden className="space-y-4">
      <div className="h-10 animate-pulse rounded bg-surface" />
      <div className="h-7 w-40 animate-pulse rounded bg-surface" />
      <div className="grid gap-x-10 gap-y-4 md:grid-cols-2">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="h-16 animate-pulse rounded bg-surface" />
        ))}
      </div>
    </div>
  );
}
