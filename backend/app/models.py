from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ImageMeta(BaseModel):
    image_id: str
    filename: str


class GenerateRequest(BaseModel):
    image_ids: list[str]


class Job(BaseModel):
    job_id: str
    images: dict[str, str] = {}  # image_id -> filepath
    canvas_path: Optional[str] = None
    status: str = "pending"  # pending | done | error
    error: Optional[str] = None
