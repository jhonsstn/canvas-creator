from __future__ import annotations
import json
import uuid
from pathlib import Path
from app.models import Job

STORAGE = Path(__file__).parent.parent / "storage"
JOBS_FILE = STORAGE / "jobs.json"

_store: dict[str, Job] = {}


def _save_store() -> None:
    STORAGE.mkdir(exist_ok=True)
    data = {jid: job.model_dump() for jid, job in _store.items()}
    JOBS_FILE.write_text(json.dumps(data, indent=2))


def _load_store() -> None:
    if not JOBS_FILE.exists():
        return
    try:
        data = json.loads(JOBS_FILE.read_text())
        for jid, job_data in data.items():
            _store[jid] = Job(**job_data)
    except Exception as e:
        print(f"Error loading jobs: {e}")


# Load on import
_load_store()


def create_job() -> Job:
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id)
    _store[job_id] = job
    _save_store()
    return job


def get_job(job_id: str) -> Job | None:
    return _store.get(job_id)


def save_job(job: Job) -> None:
    _store[job.job_id] = job
    _save_store()


def all_jobs():
    return list(_store.values())


def delete_job(job_id: str) -> bool:
    if job_id in _store:
        del _store[job_id]
        _save_store()
        return True
    return False
