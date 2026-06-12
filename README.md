# Flashcards

A spaced-repetition flashcards app. Create cards, organize them into decks, and
study with a real scheduling algorithm (FSRS) that shows you each card right
before you'd forget it.

## Features

- **FSRS spaced repetition** — grade each card Again / Hard / Good / Easy; the
  engine schedules the next review. Study a "due now" queue, optionally scoped
  to one deck.
- **Decks** — organize cards; study or filter by deck.
- **Labels** — free-form tags on cards with counts.
- **Import / export** — CSV or JSON, per deck or all cards.
- **Auth & roles** — cookie-based JWT auth with access/refresh tokens, a
  `user`/`admin` role model, rate-limited login/registration, and an admin
  panel for user role management.

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | React 19, Vite, Tailwind v4, React Router |
| Backend  | FastAPI, SQLAlchemy 2, Alembic |
| Data     | Postgres (users, cards, decks, progress) |
| Sessions | Redis (sessions + rate-limit counters) |
| SR engine| [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) |

## Architecture

```
React (Vite)  ──/api──▶  FastAPI  ──▶  Postgres   (users, cards, decks, progress)
                              │
                              └──────▶  Redis      (sessions, rate limiting)
```

- Auth uses httpOnly cookies: a short-lived access token, a refresh token, and
  a server-side session id. The frontend's API client (`src/api/client.js`)
  transparently refreshes the access token on a 401 and replays the request.
- Cards/decks/progress live in Postgres. Per-card FSRS state is stored as JSONB
  with a denormalized, indexed `due` timestamp for fast queue queries.
- Redis holds only sessions and rate-limit counters.

```
api/
  main.py            app + router wiring
  config.py          env-driven settings (fails fast on weak/missing secrets)
  database.py        SQLAlchemy engine/session
  db_models.py       ORM models (User, Card, Deck, Progress)
  models.py          Pydantic request/response schemas
  scheduler.py       FSRS wrapper (only module importing fsrs)
  routes/            auth, cards, decks, study, admin, io (import/export)
  alembic/           migrations
  tests/             pytest suite
src/
  api/client.js      central fetch client with token refresh
  context/           AuthContext
  components/, pages/
```

## Local development

### Option A — Docker Compose (everything)

```bash
echo "JWT_SECRET_KEY=$(python -c 'import secrets;print(secrets.token_urlsafe(64))')" > .env
# optional: ADMIN_EMAIL=you@example.com and ADMIN_PASSWORD=... to auto-create an admin
docker compose up --build
# open http://localhost:8080
```

### Option B — Run pieces directly

Requires local Postgres + Redis.

```bash
# Backend
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in JWT_SECRET_KEY, DATABASE_URL, etc.
alembic upgrade head
python seed_admin.py          # creates the first admin from ADMIN_EMAIL/PASSWORD
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
npm install
npm run dev                   # http://localhost:5177, proxies /api -> :8000
```

## Tests

```bash
# Backend (needs Postgres + Redis; point env at them)
cd api
pip install -r requirements-dev.txt
DATABASE_URL=postgresql+psycopg2://flashcards:flashcards@localhost:5432/flashcards \
REDIS_URL_0=redis://localhost:6379/15 \
pytest

# Frontend
npm run lint
npm test
```

CI (GitHub Actions, `.github/workflows/ci.yml`) runs all of the above on push
and PR, with Postgres and Redis service containers.

## Deployment

See [DEPLOY.md](DEPLOY.md) for the production runbook (bare-metal systemd +
Caddy, one-time Postgres provisioning, and the deploy script).
