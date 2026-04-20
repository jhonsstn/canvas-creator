# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Local dev (requires `uv` and Node 20+):

```bash
./start.sh                           # runs backend (uvicorn on :8000) + frontend (vite on :5173)
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
cd frontend && npm run build         # tsc -b && vite build
cd frontend && npm run lint          # eslint
```

Docker (production-like):

```bash
docker compose up --build -d         # frontend on ${FRONTEND_PORT:-8080}; backend not exposed
```

The frontend expects the backend at `VITE_API_BASE` (defaults to `http://localhost:8000` in dev). In Docker, nginx reverse-proxies `/health`, `/upload`, and `/jobs` to the backend on the internal `canvas_net` network, and `VITE_API_BASE` is left empty so the browser hits same-origin.

There is no test suite.

## Architecture

Two-service app. Backend composes reference images into a single PNG "sheet"; frontend is a workbench UI to upload, crop, arrange, and review results.

### Backend (`backend/app/`, FastAPI + Pillow)

- **`main.py`** — FastAPI app; CORS allows `localhost:5173` only (dev). Routes live in `api.py`.
- **`models.py`** — Pydantic models. `Job` is the unit of work (id → image paths + canvas output); `CropRect` uses normalized (0–1) coords; `GenerateRequest` carries per-image crops/scales plus an optional `global_scale` that overrides per-image scales and also widens the canvas.
- **`jobs.py`** — SQLite-backed job store at `backend/db/jobs.db` (persisted via the `canvas_db` Docker volume). Jobs are serialized as JSON blobs inside a single `jobs` table. On startup it auto-migrates a legacy `storage/jobs.json` if present, renaming it to `.json.migrated`.
- **`api.py`** — endpoints (see README). Important lifecycle details:
  - `/upload` creates a job and writes originals to `storage/<job_id>/originals/`.
  - `/jobs/{id}/generate` composes the canvas, then **deletes the originals** (`_cleanup_originals`) on both success and error. Only the final `canvas.png` is retained long-term.
  - `_sweep_abandoned` (called on each upload) deletes originals for jobs older than `ABANDON_TTL_SECONDS` (1h) that never produced a canvas.
  - `GET /jobs` only returns jobs with a canvas — jobs mid-flight or errored are hidden from the gallery.
  - `/thumb/{image_id}` accepts optional `x,y,w,h` to preview crops server-side.
- **`layout.py`** — pure layout engine. `build_canvas` arranges images in an `N_COLS=2` grid where each cell is a reference image plus an empty drawing block `DRAW_SCALE=1.5×` the ref. Per-image `scales` stretch `CELL_HEIGHT` (the reference height), and `canvas_width_scale` widens the whole canvas proportionally. Final width is multiplied by `CANVAS_WIDTH_BONUS=1.2` with the extra pixels distributed into the drawing columns (not the references). All the tunable constants (gaps, padding, drawing ratio) live at the top of this file.

### Frontend (`frontend/src/`, React 19 + React Router 7 + Vite)

- **`App.tsx`** — shell with header, nav (`/` workbench, `/gallery` archive), footer, and a 30s-interval `/health` ping for the API status badge.
- **`api.ts`** — all backend calls. Reads `VITE_API_BASE` at build time. `SCALE_PRESETS` are the allowed per-image size multipliers (0.75–3×) exposed in the UI.
- **`pages/Creator.tsx`** — main workbench: upload, order, crop, set scales, generate canvas.
- **`pages/Gallery.tsx`** — lists finished jobs from `GET /jobs`, supports delete.
- **`CropDialog.tsx`** — `react-easy-crop` wrapper. Emits normalized `CropRect` that matches the backend's `_apply_crop`. Parent re-keys the component to reset internal state.

### Data & storage

- **Originals** in `storage/<job_id>/originals/` — short-lived, deleted right after canvas generation or by the abandoned-sweep.
- **Canvases** in `storage/<job_id>/canvas.png` — the only durable artifact of a completed job.
- **Job metadata** in `db/jobs.db` (SQLite). Both paths are mounted as named Docker volumes (`canvas_storage`, `canvas_db`).

### Conventions worth knowing

- Crops are always normalized fractions (0–1) in both API and UI — never pixels — so the server can re-derive pixel boxes against the original image dimensions.
- When both `global_scale` and per-image `scales` are present, `global_scale` wins (see `api.py` generate handler) and also drives `canvas_width_scale`.
- The backend treats originals as disposable: don't build features that rely on reading them after `/generate` has run.
