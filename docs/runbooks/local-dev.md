# Local development

## API + database (Docker)

From repo root:

```bash
docker compose up --build
```

Health: `GET http://localhost:8000/health`

Migrations run on API container start (`alembic upgrade head`). To run manually:

```bash
cd apps/api && uv run alembic upgrade head
```

## API on host, DB in Docker

```bash
docker compose up -d db
cd apps/api && uv sync --all-extras && uv run uvicorn homehub.main:app --reload --app-dir src
```

## Mobile on LAN

1. Start the API so it listens on `0.0.0.0:8000` (Docker default).
2. Find your PC LAN IP (e.g. `192.168.1.x`).
3. Configure the app to use `http://<LAN-IP>:8000` when M1+ adds API client settings.
4. Sideload builds: use Android Studio / Xcode per platform docs when you enable device testing.

## Tests

```bash
cd apps/api && uv run ruff check . && uv run pytest
cd apps/mobile && npm test && npm run typecheck
```
