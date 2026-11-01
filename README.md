# Forkful

Forkful is a food delivery web app for Lviv. Customers browse restaurants, order with standard, express or pickup delivery, pay online (Stripe test mode) or in cash, and watch the courier on a map. Couriers get a simple workspace; admins manage the catalog, orders, couriers, loyalty rules and reports.

It is a course project for "Software Documentation and Design Patterns" (Lviv Polytechnic, variant 8). It applies twelve GoF patterns in a layered Flask backend with a Next.js frontend; see [docs/patterns.md](docs/patterns.md).

## Features

**Catalog**
- Restaurants with menus grouped by category, ratings and reviews.
- Filters for cuisine, price level, maximum delivery time and minimum rating; sorting by rating, delivery time or price. The filters live in the URL, so a filtered view can be reloaded or shared.

**Ordering and payment**
- A cart limited to one restaurant, then checkout with a live price breakdown.
- Delivery: standard, express (higher fee, shorter ETA) or pickup. The delivery point is picked on a map and must be inside the delivery zone.
- Payment by card online (Stripe Checkout, or a mock gateway without keys) or in cash.
- Validation errors from the server are shown next to the field they concern.

**Account**
- Order history and order details, one-click reorder (it reports dishes that are sold out or have changed price), cancellation before the kitchen starts.
- Favorite restaurants, profile and password, reviews of delivered orders.

**Loyalty**
- Bonus points for delivered orders, redeemable at checkout (up to a cap).
- An automatic discount for regular customers.
- A premium card with free delivery, bought through the same payment flow.

**Tracking and notifications**
- A map with the restaurant, the destination, the courier's road route and current position, and a status timeline.
- In-app notifications (bell in the header): accepted, preparing, ready, on the way, delivered, cancelled, points earned, promotions.

**Courier workspace**
- Orders ready for pickup; take an order, mark it picked up (the road route is built at that moment) and delivered.

**Admin**
- Restaurants, dishes and cuisines: create, edit, activate or deactivate.
- Courier accounts.
- An order board with filters, and order pages with only the valid status buttons.
- Loyalty settings and promotions to all customers.
- Reports (sales by restaurant, popular dishes, courier performance) with a period picker and CSV export.

## Tech stack

| Part | Stack |
|---|---|
| Backend | Python 3.12, Flask 3 (app factory + blueprints, `/api/v1`), SQLAlchemy 2, Flask-Migrate, Pydantic 2, Flask-JWT-Extended, stripe, requests, Ruff |
| Frontend | Next.js 16 (App Router), React 19, TypeScript (strict), Tailwind CSS 4, SWR, react-leaflet + OpenStreetMap, lucide-react |
| Database | PostgreSQL 16 in Docker Compose |
| External | Stripe (test mode, optional), OSRM public routing server (with an offline fallback) |

The reasons for each choice are in [docs/tech-stack.md](docs/tech-stack.md).

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.12 | `python --version` (`py -3.12 --version` on Windows) |
| Node.js | 20 or newer (tested with 22) | `node --version` |
| npm | 10 or newer | `npm --version` |
| Docker Desktop (or Docker Engine + Compose) | any recent | `docker compose version` |
| Git | any | `git --version` |

Ports 3000 (frontend), 5000 (backend) and 5432 (PostgreSQL) must be free.

## Running locally

All commands start in the repository root unless they say otherwise.

### 1. Get the code

```bash
git clone <repository-url> forkful
cd forkful
```

### 2. Start PostgreSQL

Start Docker Desktop first, then:

```bash
docker compose up -d postgres
```

This starts `postgres:16-alpine` as `forkful-postgres` on port 5432, with database, user and password all set to `forkful`. Data is kept in the `postgres_data` volume. Stop it with `docker compose stop`; `docker compose down -v` also deletes the data.

### 3. Set up the backend

Create a virtual environment and install the dependencies.

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

macOS / Linux (or Git Bash on Windows, using `source .venv/Scripts/activate`):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Copy the environment file. The defaults work with the Docker database and need no changes:

```bash
cp backend/.env.example backend/.env
```

Create the tables and load the demo data:

```bash
cd backend
flask --app app db upgrade
python seed.py
```

The seed is idempotent: running it again only adds what is missing. It prints `Seed complete: 5 users, 10 restaurants, 8 cuisines, 9 new orders.` the first time (`0 new orders` afterwards).

Start the API (still in `backend/`, with the virtual environment active):

```bash
flask --app app run --port 5000
```

Check it: `curl http://127.0.0.1:5000/api/v1/health` returns `{"service": "forkful-backend", "status": "ok"}`.

### 4. Set up the frontend

In a second terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. The frontend forwards `/api/*` to the backend at `API_PROXY_TARGET` (default `http://127.0.0.1:5000`), so the backend must be running.

For a production build: `npm run build && npm run start`.

## Demo accounts

All seeded accounts use the password **`forkful123`**.

| Role | Email | What to try |
|---|---|---|
| Admin | `admin@example.com` | Admin → Orders, Restaurants, Couriers, Loyalty, Promotions, Reports |
| Courier | `taras.courier@example.com` | `/courier`: take, pick up, deliver |
| Courier | `andrii.courier@example.com` | Same, as a second courier |
| Customer | `olena@example.com` | Regular customer with a premium card, points and order history |
| Customer | `maksym@example.com` | Customer with a short history |

The seed contains:
- 10 restaurants in central Lviv (real coordinates) across 8 cuisines, about 100 dishes;
- past orders with status history, reviews, favorites, points and notifications.

Restaurants have no photos; the UI shows a colored cover with the restaurant's initial.

A full flow: sign in as Olena, order from any restaurant with standard delivery and cash. Then as admin open Orders → the new order → "Start preparing" → "Ready for a courier". As Taras, take it and press "Picked up", and watch the courier move on Olena's order page. Finally press "Delivered" and see the points in Olena's account.

## Payments

**Without keys (default).** If `STRIPE_SECRET_KEY` is empty, "Card online" uses a mock gateway. It goes through the same success page and confirmation as Stripe and always succeeds. Cash orders are accepted immediately and marked paid on delivery.

**With Stripe test mode.**
1. Create a free account at https://dashboard.stripe.com and switch on **Test mode**.
2. Developers → API keys: copy the **secret key** (`sk_test_...`) into `backend/.env` as `STRIPE_SECRET_KEY`.
3. Restart the backend. "Card online" now opens Stripe Checkout.
4. Pay with the test card **`4242 4242 4242 4242`**, any future expiry date, any CVC and any postcode. The card `4000 0000 0000 0002` is declined, if you want to test a failure.

After paying, Stripe sends the customer to `FRONTEND_URL/checkout/success?session_id=...`. The backend checks the session with Stripe and moves the order from "waiting for payment" to "accepted". Cancelling a paid order refunds it in Stripe. Never use live keys.

## Environment variables

`backend/.env` (template: [`backend/.env.example`](backend/.env.example)):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://forkful:forkful@localhost:5432/forkful` | Database connection. If the variable is missing entirely, the app falls back to a local SQLite file (`backend/instance/forkful.db`) for a quick look; PostgreSQL is the supported database. |
| `SECRET_KEY` | dev placeholder | Flask secret. Set a random string of 32+ characters outside local development. |
| `JWT_SECRET_KEY` | dev placeholder | Signs access tokens. Random, 32+ characters. |
| `JWT_ACCESS_TOKEN_HOURS` | `12` | Token lifetime in hours. |
| `STRIPE_SECRET_KEY` | empty | Stripe test key `sk_test_...`. Empty means the mock gateway. |
| `FRONTEND_URL` | `http://localhost:3000` | Where Stripe returns the customer after paying. |
| `DELIVERY_RADIUS_KM` | `7` | Delivery zone radius from each restaurant. |
| `OSRM_BASE_URL` | `https://router.project-osrm.org` | Routing server for courier routes. If unreachable, a straight line is used. |

`frontend/.env.local` (template: [`frontend/.env.example`](frontend/.env.example)):

| Variable | Default | Description |
|---|---|---|
| `API_PROXY_TARGET` | `http://127.0.0.1:5000` | Flask server that `/api/*` is forwarded to (server side only). |

`.env` files are git-ignored. Don't commit real keys.

## Project structure

```text
backend/
  app/
    __init__.py         create_app(): config, extensions, blueprints, error handlers, observers
    config.py           settings from environment variables
    container.py        manual dependency injection: builds and wires all services
    api/                blueprints under /api/v1, JWT role checks, error handler
    schemas/            Pydantic request/response models
    services/           use cases: CheckoutFacade, OrderService, PaymentService, ...
    domain/             patterns and business rules (no Flask, no SQLAlchemy)
      catalog/  delivery/  events/  orders/  payments/  pricing/  reports/
    repositories/       all database queries
    models/             SQLAlchemy models
  migrations/           Alembic migrations
  seed.py, seed_data.py idempotent demo data for Lviv
  requirements.txt, pyproject.toml (Ruff), .env.example
frontend/
  app/                  pages: catalog, restaurants/[id], cart, checkout, orders, account,
                        favorites, login, register, courier, admin/*
  components/           UI components by area
  lib/                  API client, auth, cart store, formatters, hooks
  types/                API types
  next.config.ts        /api/* rewrite to Flask
docs/
  patterns.md           the twelve GoF patterns, where and why
  architecture.md       layers, SOLID, GRASP, REST API reference
  tech-stack.md         technologies and reasons
  diagrams/             PlantUML sources (.puml) and rendered PNGs
docker-compose.yml      PostgreSQL 16
```

## Documentation

- [docs/patterns.md](docs/patterns.md): each pattern's problem, participants, wiring, collaboration and a code excerpt.
- [docs/architecture.md](docs/architecture.md): layers, SOLID and GRASP with class names, the full endpoint table.
- [docs/tech-stack.md](docs/tech-stack.md): technologies and why they were chosen.
- Diagrams in [docs/diagrams/](docs/diagrams/):
  - [use cases](docs/diagrams/use-case.png)
  - [class diagram](docs/diagrams/class-diagram.png), with patterns marked by color, plus two focused views: [checkout](docs/diagrams/class-diagram-checkout.png) and [lifecycle](docs/diagrams/class-diagram-lifecycle.png)
  - [order states](docs/diagrams/order-state.png)
  - [checkout sequence](docs/diagrams/checkout-sequence.png)
  - [architecture](docs/diagrams/architecture.png)
  - [database schema](docs/diagrams/er-diagram.png)

### Rendering the diagrams

The PNGs are committed. To re-render them after editing a `.puml` file, either:

- **Docker** (no Java needed), from the repository root:

  ```bash
  docker run --rm -e PLANTUML_LIMIT_SIZE=16384 -v "$(pwd)/docs/diagrams:/data" plantuml/plantuml:latest -tpng "/data/*.puml"
  ```

  On Windows PowerShell use `-v "${PWD}/docs/diagrams:/data"`. In Git Bash prefix the command with `MSYS_NO_PATHCONV=1`.

- **VS Code**: install the "PlantUML" extension (jebbs.plantuml), open a `.puml` file and run "PlantUML: Export Current Diagram". This needs Java, or set the extension's renderer to the PlantUML server.

`patterns-palette.iuml` holds the shared pattern colors and the legend, and every class diagram includes it. `class-diagram-checkout.puml` and `class-diagram-lifecycle.puml` include the full diagram and filter it by tag, so they stay in sync with it.

## Useful commands

```bash
# backend: lint, format check, models vs migrations
cd backend
ruff check . && ruff format --check .
flask --app app db check

# sign in and call a protected endpoint
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "olena@example.com", "password": "forkful123"}'
curl http://127.0.0.1:5000/api/v1/auth/me -H "Authorization: Bearer <access_token>"

# frontend: types (generates the route types first), lint, production build
cd frontend
npm run typecheck && npm run lint && npm run build
```

## Troubleshooting

- **`connection refused` on port 5432**: Docker Desktop isn't running, or the container is stopped. Start Docker and run `docker compose up -d postgres`.
- **The frontend shows "Can't reach the server"**: the backend isn't running on port 5000, or `API_PROXY_TARGET` points elsewhere.
- **`npm run dev` or `npm run build` exits with a Next.js security notice**: the first run on a machine prints an upgrade reminder for Next.js 16.4.0 and stops; run the same command again and it starts normally.
- **Courier routes are straight lines**: the OSRM demo server didn't answer in time. That is the intended fallback; tracking still works.
- **Start over with fresh data**: `docker compose down -v`, then `docker compose up -d postgres` and repeat `flask --app app db upgrade` and `python seed.py`.
