# Deployment (production)

Prod runs **bare-metal**: systemd services (`flashcardsapi`, `flashcardscaddy`)
+ Caddy serving the built frontend and terminating TLS. Postgres and Redis run
on the box. (The `docker-compose.yml` in the repo is for local dev only.)

Recurring deploys use [`deploy.sh`](deploy.sh): `git pull` → build frontend →
restart Caddy → `pip install` → **`alembic upgrade head`** → restart API.

---

## One-time setup (before the first Phase-2 deploy)

The app now **fails to boot** without a strong `JWT_SECRET_KEY` and a reachable
Postgres. Do this once on a fresh prod box:

```bash
# 1. Provision Postgres
sudo apt install -y postgresql
sudo -u postgres psql -c "CREATE USER flashcards WITH PASSWORD 'a-strong-db-password';"
sudo -u postgres psql -c "CREATE DATABASE flashcards OWNER flashcards;"

# 2. Configure api/.env (see api/.env.example). Required:
#    DATABASE_URL=postgresql+psycopg2://flashcards:a-strong-db-password@localhost:5432/flashcards
#    JWT_SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(64))">
#    ENVIRONMENT=production           # cookies become Secure — requires HTTPS (Caddy provides it)
#    CORS_ORIGINS=https://your.domain
#    REDIS_URL_0=redis://localhost:6379/0
#    ADMIN_EMAIL=you@example.com       # optional: auto-creates the first admin on deploy
#    ADMIN_PASSWORD=a-strong-admin-password

# 3. Initial migration + admin
cd /home/omni/flashcards/api && source .venv/bin/activate
alembic upgrade head
python seed_admin.py      # idempotent; also runs if ADMIN_* are set
```

After that, `deploy.sh` handles everything on each push to `main`.

## Notes

- **Fresh start:** users/cards/progress moved from Redis to Postgres with no
  data migration. Any pre-existing data in Redis is abandoned (not deleted).
- **Redis is still required** — sessions and rate-limit counters live there.
- **Secret rotation:** changing `JWT_SECRET_KEY` invalidates all existing
  access/refresh tokens (everyone is logged out). That's expected.
- The first admin can only be created via `seed_admin.py` (no public admin
  registration). Regular users self-register at `/auth/register` and always get
  the `user` role.
