# Tech stack

## Backend

| Technology | Version | Used for | Why |
|---|---|---|---|
| Python | 3.12 | Language | Modern typing (`type` parameters, `X \| None`, `Protocol`). The domain layer relies on generics such as `ReportGenerator[RecordT, GroupT]` and `Command[ResultT]`. |
| Flask | 3.0 | HTTP layer | Small and explicit. The app factory (`create_app`) plus blueprints keep HTTP code thin and separate from the use cases, which suits a layered architecture better than a batteries-included framework. |
| SQLAlchemy | 2.x | ORM | Typed `Mapped[...]` models, explicit queries in repositories, row locks (`with_for_update`) for checkout, status changes and points. |
| Flask-SQLAlchemy | 3.1 | Session per request | Ties the session to the Flask app context. |
| Flask-Migrate (Alembic) | 4.0 | Schema migrations | Versioned schema in `backend/migrations/`. `flask db check` verifies the models and migrations agree. |
| PostgreSQL | 16 | Database | Constraints (CHECK, UNIQUE, FK with CASCADE / SET NULL), row locks, JSON for the route polyline. Runs in Docker Compose. |
| psycopg | 3 | PostgreSQL driver | Current driver, binary wheels for Windows/macOS/Linux. |
| Pydantic | 2 | Request/response schemas | Validates query strings and bodies with field-level errors (shown inline in forms) and serializes responses. |
| Flask-JWT-Extended | 4.6 | Authentication | Stateless access tokens carrying the user's role. `roles_required` restricts endpoints to customer, courier or admin. |
| stripe | 10.x | Online payments | Stripe Checkout in test mode, wrapped by `StripeGateway` (Adapter). Optional: without a key, `MockGateway` is used. |
| requests | 2.32 | OSRM calls | Fetches road routes. Wrapped by `OsrmRouteProvider` (Adapter) with a timeout and a straight-line fallback. |
| python-dotenv | 1.0 | Configuration | Loads `backend/.env` for every entry point (Flask CLI, `seed.py`). |
| Ruff | 0.5 | Lint and format | One fast tool for style and common bugs; configured in `backend/pyproject.toml` (line length 100). |

## Frontend

| Technology | Version | Used for | Why |
|---|---|---|---|
| Next.js (App Router) | 16 | Pages, routing, build | File-based routes for each area (catalog, checkout, tracking, courier, admin). `next.config.ts` rewrites `/api/*` to Flask, so there is one origin and no CORS. |
| React | 19 | UI | — |
| TypeScript | 5, `strict: true` | Types | API types in `types/` are shared by every page and component; no `any`. |
| Tailwind CSS | 4 | Styling | Theme tokens (cream background, tomato accent, espresso text, sage, saffron) defined once in `app/globals.css` and used everywhere. |
| SWR | 2.5 | Data fetching | Caches by API path, revalidates after mutations, polls with `refreshInterval`: tracking every 5 s while the order is active, the courier workspace every 10 s, notifications and the admin board every 15 s. |
| Leaflet + react-leaflet | 1.9 / 5 | Maps | Delivery point picker at checkout, route and courier marker on the tracking page. OpenStreetMap tiles need no API key. Loaded client-side only (`next/dynamic`, `ssr: false`). |
| lucide-react | — | Icons | One consistent, light icon set, used sparingly. |
| next/font | — | Fonts | Fraunces (headings) and Geist (UI text), self-hosted by Next.js. |
| ESLint (`eslint-config-next`) | 9 | Lint | Next.js and React rules. |

## Infrastructure and external services

| Service | Used for | Notes |
|---|---|---|
| Docker Compose | PostgreSQL 16 for local development | `docker compose up -d postgres`; data persists in the `postgres_data` volume. |
| Stripe (test mode) | Card payments and refunds | Optional. Test card `4242 4242 4242 4242`. Verification happens when the customer returns to `/checkout/success`. |
| OSRM public demo server | Road route when a courier picks up an order | `router.project-osrm.org`, configurable with `OSRM_BASE_URL`. If it is slow or down, the route falls back to a straight line. |
| OpenStreetMap tiles | Map background | Loaded by the browser. |
| PlantUML (Docker image `plantuml/plantuml`) | Rendering `docs/diagrams/*.puml` | Development only; see the README. |

## Choices worth explaining

- **Money in integer kopiyky.** Avoids floating-point rounding in discounts and points. Stripe also takes amounts in minor units.
- **Manual dependency injection.** `app/container.py` wires about fifteen classes. That is small enough that a DI framework would add more indirection than it saves, and the wiring stays readable in one file.
- **Status side effects run synchronously.** Observers write history, notifications and points in the same transaction as the status change. The project has no message broker, which keeps the setup to one database, and a failed side effect rolls the change back instead of leaving it half-done.
- **Simulated courier position.** The position is computed on each request from the stored route and the time since pick-up, so there are no background workers or WebSockets. The tracking page polls every 5 seconds.
- **JWT in `localStorage`.** Simple to send as a `Bearer` header through the Next.js proxy. The tradeoff is exposure to injected scripts; an httpOnly cookie would need CSRF protection on top.
