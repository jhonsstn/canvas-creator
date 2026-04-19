from __future__ import annotations
import json
import sqlite3
import uuid
from pathlib import Path
from app.models import Job

DB_DIR = Path(__file__).parent.parent / "db"
DB_FILE = DB_DIR / "jobs.db"

LEGACY_JOBS_FILE = Path(__file__).parent.parent / "storage" / "jobs.json"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")


def _migrate_legacy_json() -> None:
    if not LEGACY_JOBS_FILE.exists():
        return
    try:
        data = json.loads(LEGACY_JOBS_FILE.read_text())
        with _connect() as conn:
            for jid, job_data in data.items():
                job = Job(**job_data)
                conn.execute(
                    "INSERT OR IGNORE INTO jobs (job_id, data, created_at) VALUES (?, ?, ?)",
                    (job.job_id, job.model_dump_json(), job.created_at),
                )
        LEGACY_JOBS_FILE.rename(LEGACY_JOBS_FILE.with_suffix(".json.migrated"))
    except Exception as e:
        print(f"Error migrating legacy jobs.json: {e}")


_init_db()
_migrate_legacy_json()


def _row_to_job(row: sqlite3.Row) -> Job:
    return Job(**json.loads(row["data"]))


def create_job() -> Job:
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO jobs (job_id, data, created_at) VALUES (?, ?, ?)",
            (job.job_id, job.model_dump_json(), job.created_at),
        )
    return job


def get_job(job_id: str) -> Job | None:
    with _connect() as conn:
        row = conn.execute("SELECT data FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    return _row_to_job(row) if row else None


def save_job(job: Job) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs (job_id, data, created_at) VALUES (?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET data = excluded.data
            """,
            (job.job_id, job.model_dump_json(), job.created_at),
        )


def all_jobs() -> list[Job]:
    with _connect() as conn:
        rows = conn.execute("SELECT data FROM jobs ORDER BY created_at DESC").fetchall()
    return [_row_to_job(r) for r in rows]


def delete_job(job_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    return cur.rowcount > 0
