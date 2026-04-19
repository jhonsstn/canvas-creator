#!/bin/bash
# Run backend and frontend concurrently
set -e
trap 'kill 0' EXIT INT TERM

cd "$(dirname "$0")"
(cd backend && uv run uvicorn app.main:app --reload --port 8000) &
(cd frontend && npm run dev) &
wait
