# Canvas Creator

A self-hosted workbench for composing multiple reference images into a single drawing sheet.

## Features

- Upload multiple images, arrange them, and generate a single canvas PNG
- Non-destructive per-image crop before compositing
- Gallery archive with persistent job storage
- Live API status badge in the UI header
- Single-command Docker deployment

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12 · FastAPI · Pillow |
| Frontend | React 19 · TypeScript · Vite · React Router |
| Serving | Nginx (reverse proxy + static files) |
| Runtime | Docker Compose |

## Running locally

Requires [uv](https://github.com/astral-sh/uv) and Node 20+.

```bash
./start.sh
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Running with Docker

```bash
cp .env.example .env          # adjust FRONTEND_PORT if needed
docker compose up --build -d
```

The app is served at `http://localhost:8080` (or whatever `FRONTEND_PORT` is set to). Nginx proxies API calls to the backend on the internal network — no ports are exposed for the backend directly.

Canvas files are persisted in a named Docker volume (`canvas_storage`).

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — returns `{"status":"ok","uptime":<s>}` |
| `POST` | `/upload` | Upload images, creates a new job |
| `POST` | `/jobs/{job_id}/generate` | Compose uploaded images into a canvas |
| `GET` | `/jobs/{job_id}/canvas.png` | Download the generated canvas |
| `GET` | `/jobs` | List jobs that have a canvas |
| `DELETE` | `/jobs/{job_id}` | Delete a job and its files |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `FRONTEND_PORT` | `8080` | Host port for the frontend container |
