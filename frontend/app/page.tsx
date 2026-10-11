const quickFilters = [
  "Italian",
  "Japanese",
  "Ukrainian",
  "Fast delivery",
  "Under 20 min",
];

const restaurantCards = [
  { name: "Mamma Rosa", cuisine: "Italian", eta: "25–35 min", rating: "4.8" },
  { name: "Sora Sushi", cuisine: "Japanese", eta: "20–30 min", rating: "4.9" },
  { name: "Borshchivka", cuisine: "Ukrainian", eta: "30–40 min", rating: "4.7" },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <section className="mx-auto grid max-w-6xl gap-8 px-6 pb-12 pt-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8 lg:py-12">
        <div className="flex flex-col justify-center">
          <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28rem] text-[var(--sage)]">
            Lviv food delivery
          </p>
          <h1 className="max-w-xl font-serif text-5xl leading-none tracking-tight text-[var(--ink)] sm:text-6xl">
            Fresh dishes from the city you already know.
          </h1>
          <p className="mt-5 max-w-lg text-lg leading-8 text-[var(--muted-ink)]">
            Discover neighborhood favorites, build your cart, and track the order from the kitchen to your door.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            {quickFilters.map((item) => (
              <span
                key={item}
                className="rounded-full border border-[var(--border)] bg-white/60 px-3 py-1.5 text-sm text-[var(--muted-ink)]"
              >
                {item}
              </span>
            ))}
          </div>

          <div className="mt-10 flex flex-wrap gap-4">
            <a
              href="#restaurants"
              className="rounded-full bg-[var(--accent)] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-strong)]"
            >
              Browse restaurants
            </a>
            <a
              href="#features"
              className="rounded-full border border-[var(--border)] bg-white/70 px-6 py-3 text-sm font-semibold text-[var(--ink)] transition hover:bg-white"
            >
              Explore checkout
            </a>
          </div>
        </div>

        <div className="grid gap-4 rounded-[28px] border border-[var(--border)] bg-[var(--card)] p-5 shadow-[0_24px_60px_rgba(34,25,22,0.08)]">
          <div className="rounded-[22px] bg-[var(--surface)] p-4">
            <div className="mb-4 flex items-center justify-between text-sm text-[var(--muted-ink)]">
              <span>Today&apos;s picks</span>
              <span>Updated 4 min ago</span>
            </div>

            <div className="space-y-4">
              {restaurantCards.map((restaurant) => (
                <div
                  key={restaurant.name}
                  className="flex items-center justify-between rounded-2xl border border-[var(--border)] bg-white px-4 py-3"
                >
                  <div>
                    <p className="font-semibold text-[var(--ink)]">{restaurant.name}</p>
                    <p className="text-sm text-[var(--muted-ink)]">{restaurant.cuisine}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-[var(--sage)]">⭐ {restaurant.rating}</p>
                    <p className="text-xs text-[var(--muted-ink)]">{restaurant.eta}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-2xl bg-[var(--muted)] p-3">
              <p className="font-serif text-2xl text-[var(--ink)]">1.2k</p>
              <p className="text-xs text-[var(--muted-ink)]">orders</p>
            </div>
            <div className="rounded-2xl bg-[var(--muted)] p-3">
              <p className="font-serif text-2xl text-[var(--ink)]">4.9</p>
              <p className="text-xs text-[var(--muted-ink)]">rating</p>
            </div>
            <div className="rounded-2xl bg-[var(--muted)] p-3">
              <p className="font-serif text-2xl text-[var(--ink)]">18m</p>
              <p className="text-xs text-[var(--muted-ink)]">avg ETA</p>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-6 py-8 lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-3xl border border-[var(--border)] bg-white p-5">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--sage)]">Catalog</p>
            <h2 className="mt-3 font-serif text-3xl text-[var(--ink)]">Curated favorites</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted-ink)]">
              Filter by cuisine, price, delivery time, and rating without leaving the home page.
            </p>
          </div>
          <div className="rounded-3xl border border-[var(--border)] bg-white p-5">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--sage)]">Checkout</p>
            <h2 className="mt-3 font-serif text-3xl text-[var(--ink)]">Live pricing</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted-ink)]">
              Quote fees, estimated arrival times, and loyalty discounts before you pay.
            </p>
          </div>
          <div className="rounded-3xl border border-[var(--border)] bg-white p-5">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--sage)]">Tracking</p>
            <h2 className="mt-3 font-serif text-3xl text-[var(--ink)]">See every step</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted-ink)]">
              Follow the courier route and watch status changes as the order moves to your address.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
