# Forkful

Forkful is the food delivery service for the course project. The repository contains the Flask backend, the Next.js frontend, and the Docker Compose setup for PostgreSQL.

## Project goals

- Restaurant catalog with cuisine and delivery filters.
- Cart and checkout flow with delivery options and payment methods.
- Order lifecycle tracking, courier workflow, and account page.
- Loyalty, notifications, admin management, and reporting in later stages.

## Tech stack

- Backend: Python 3.12, Flask, SQLAlchemy 2.x, Flask-Migrate, JWT
- Frontend: Next.js 16, TypeScript, Tailwind CSS
- Database: PostgreSQL 16 via Docker Compose

## Prerequisites

- Python 3.12
- Node.js 20+
- npm
- Docker Desktop if you want to run PostgreSQL via Compose

## Local setup

1. Clone the repository and open the folder.
2. Create the virtual environment:

   ```bash
   py -3.12 -m venv .venv
   . .venv/Scripts/activate
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

3. Copy the environment samples:

   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

4. Start PostgreSQL:

   ```bash
   docker compose up -d postgres
   ```

5. Apply the migrations and load the demo data:

   ```bash
   cd backend
   flask --app app db upgrade
   python seed.py
   ```

   `backend/.env` is loaded automatically. The seed is idempotent: running it again only adds rows that are missing.

6. Start the backend:

   ```bash
   python -m flask run --host 0.0.0.0 --port 5000
   ```

7. In another terminal, start the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

8. Open `http://localhost:3000` to view the app.

## Demo accounts

All seeded accounts use the password `forkful123`.

| Role | Email |
|---|---|
| Admin | `admin@example.com` |
| Courier | `taras.courier@example.com`, `andrii.courier@example.com` |
| Customer (regular, premium card, order history) | `olena@example.com` |
| Customer (short history) | `maksym@example.com` |

The seed creates 10 restaurants in central Lviv across 8 cuisines, about 100 dishes, past orders with status history, reviews, favorites and loyalty points. Money is stored as integer kopiyky (1 UAH = 100).

## Payments

The app runs without any payment keys: when `STRIPE_SECRET_KEY` is empty, "Card online" uses a mock gateway that behaves like a successful card payment (it goes through the same success page and confirmation as Stripe).

To use real Stripe test mode:

1. Create a free account at https://dashboard.stripe.com and switch to **Test mode**.
2. Copy the secret key (`sk_test_...`) from Developers → API keys into `backend/.env` as `STRIPE_SECRET_KEY`.
3. Restart the backend and place an order with "Card online". Stripe Checkout opens; pay with the test card `4242 4242 4242 4242`, any future expiry date, any CVC.

`FRONTEND_URL` (default `http://localhost:3000`) is where Stripe sends the customer back after paying. Cash orders are confirmed immediately and paid on delivery or at pickup.

## Default runtime note

The backend code falls back to an SQLite database when `DATABASE_URL` is absent so the project can start cleanly in a minimal local environment. The repository still includes the PostgreSQL Docker Compose configuration that the full course project expects.

## Project structure

```text
backend/
  app/
  migrations/
  seed.py
  seed_data.py
  requirements.txt
  .env.example
frontend/
  app/
  public/
  package.json
  next.config.ts
docker-compose.yml
README.md
```

## Useful commands

```bash
# backend health check
curl http://127.0.0.1:5000/api/v1/health

# sign in and call a protected endpoint with the returned token
curl -X POST http://127.0.0.1:5000/api/v1/auth/login   -H "Content-Type: application/json"   -d '{"email": "olena@example.com", "password": "forkful123"}'
curl http://127.0.0.1:5000/api/v1/auth/me -H "Authorization: Bearer <access_token>"

# frontend production build
cd frontend && npm run build
```
