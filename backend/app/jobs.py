from __future__ import annotations
import uuid
from app.models import Job

_store: dict[str, Job] = {}


def create_job() -> Job:
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id)
    _store[job_id] = job
    return job


def get_job(job_id: str) -> Job | None:
    return _store.get(job_id)


def save_job(job: Job) -> None:
    _store[job.job_id] = job
