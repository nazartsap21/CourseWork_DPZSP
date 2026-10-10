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

5. Apply the initial migration:

   ```bash
   cd backend
   export FLASK_APP=app
   export SECRET_KEY=change-me
   export JWT_SECRET_KEY=change-me-too
   export DATABASE_URL=postgresql+psycopg://forkful:forkful@localhost:5432/forkful
   flask db init
   flask db migrate -m "initial scaffold"
   flask db upgrade
   ```

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

## Default runtime note

The backend code falls back to an SQLite database when `DATABASE_URL` is absent so the project can start cleanly in a minimal local environment. The repository still includes the PostgreSQL Docker Compose configuration that the full course project expects.

## Project structure

```text
backend/
  app/
  migrations/
  requirements.txt
  .env.example
frontend/
  app/
  public/
  package.json
  next.config.ts
docker-compose.yml
README.md
PROGRESS.md
```

## Useful commands

```bash
# backend health check
curl http://127.0.0.1:5000/api/v1/health

# frontend production build
cd frontend && npm run build
```
