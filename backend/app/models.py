from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class ImageMeta(BaseModel):
    image_id: str
    filename: str


class CropRect(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    w: float = Field(gt=0.0, le=1.0)
    h: float = Field(gt=0.0, le=1.0)


class GenerateRequest(BaseModel):
    image_ids: list[str]
    crops: dict[str, CropRect] = {}


class Job(BaseModel):
    job_id: str
    images: dict[str, str] = {}  # image_id -> filepath
    canvas_path: Optional[str] = None
    status: str = "pending"  # pending | done | error
    error: Optional[str] = None
