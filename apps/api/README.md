# HomeHub API

FastAPI application. Entry: `src/homehub/main.py`.

```bash
uv sync --all-extras
uv run ruff check .
uv run pytest
uv run uvicorn homehub.main:app --reload --app-dir src
```
