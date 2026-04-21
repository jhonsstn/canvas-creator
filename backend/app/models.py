from __future__ import annotations
import time
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
    scales: dict[str, float] = {}
    global_scale: Optional[float] = None
    show_grid: bool = False


class RecomposeRequest(BaseModel):
    global_scale: Optional[float] = None
    show_grid: bool = False


class Job(BaseModel):
    job_id: str
    images: dict[str, str] = {}  # image_id -> filepath
    canvas_path: Optional[str] = None
    canvas_w: Optional[int] = None
    canvas_h: Optional[int] = None
    status: str = "pending"  # pending | done | error
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    # Persisted generate inputs for re-compose
    image_order: list[str] = []
    crops: dict[str, CropRect] = {}
    scales: dict[str, float] = {}
    global_scale: Optional[float] = None
    show_grid: bool = False
    originals_expire_at: Optional[float] = None
