from __future__ import annotations
import io
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, Response
from PIL import Image

from app.jobs import all_jobs, create_job, get_job, save_job, delete_job
from app.models import GenerateRequest, RecomposeRequest, CropRect, Job
from app.layout import build_canvas

router = APIRouter()

STORAGE = Path(__file__).parent.parent / "storage"
STORAGE.mkdir(exist_ok=True)

_START_TIME = time.time()


@router.get("/health")
def health():
    return {"status": "ok", "uptime": round(time.time() - _START_TIME)}


@router.get("/jobs")
def list_jobs():
    jobs = [
        {
            "job_id": j.job_id,
            "created_at": j.created_at,
            "status": j.status,
            "has_canvas": j.canvas_path is not None,
            "canvas_size": [j.canvas_w, j.canvas_h] if j.canvas_w and j.canvas_h else None,
        }
        for j in all_jobs()
        if j.canvas_path is not None
    ]
    # Sort by newest first
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return jobs


@router.get("/jobs/{job_id}")
def job_detail(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "has_canvas": job.canvas_path is not None,
        "canvas_size": [job.canvas_w, job.canvas_h] if job.canvas_w and job.canvas_h else None,
        "originals_available": bool(job.images),
        "global_scale": job.global_scale,
        "show_grid": job.show_grid,
        "image_order": job.image_order,
    }


@router.delete("/jobs/{job_id}")
def remove_job(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    # Delete physical files
    job_dir = STORAGE / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)

    # Remove from store
    delete_job(job_id)
    return {"success": True}


ORIGINALS_TTL_SECONDS = 30 * 60  # originals kept for 30 min after generate (or after upload if abandoned)


def _cleanup_originals(job: Job) -> None:
    originals_dir = STORAGE / job.job_id / "originals"
    if originals_dir.exists():
        shutil.rmtree(originals_dir, ignore_errors=True)
    job.images = {}
    save_job(job)


def _sweep_abandoned() -> None:
    now = time.time()
    for job in list(all_jobs()):
        if not job.images:
            continue
        # Abandoned upload: no canvas produced within TTL
        if job.canvas_path is None and now - job.created_at > ORIGINALS_TTL_SECONDS:
            _cleanup_originals(job)
        # Generated but originals TTL has passed
        elif job.originals_expire_at is not None and now > job.originals_expire_at:
            _cleanup_originals(job)


def _apply_crop(img: Image.Image, crop: CropRect) -> Image.Image:
    iw, ih = img.size
    left = int(round(crop.x * iw))
    top = int(round(crop.y * ih))
    right = int(round((crop.x + crop.w) * iw))
    bottom = int(round((crop.y + crop.h) * ih))
    left = max(0, min(left, iw - 1))
    top = max(0, min(top, ih - 1))
    right = max(left + 1, min(right, iw))
    bottom = max(top + 1, min(bottom, ih))
    return img.crop((left, top, right, bottom))


@router.post("/upload")
async def upload_images(files: list[UploadFile] = File(...)):
    _sweep_abandoned()
    job = create_job()
    job_dir = STORAGE / job.job_id / "originals"
    job_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for f in files:
        image_id = str(uuid.uuid4())
        ext = Path(f.filename or "image.jpg").suffix or ".jpg"
        dest = job_dir / f"{image_id}{ext}"
        contents = await f.read()
        dest.write_bytes(contents)
        job.images[image_id] = str(dest)
        results.append({"image_id": image_id, "filename": f.filename, "job_id": job.job_id})

    save_job(job)
    return {"job_id": job.job_id, "images": results}


@router.post("/jobs/{job_id}/generate")
def generate(job_id: str, req: GenerateRequest):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    try:
        images: list[Image.Image] = []
        for image_id in req.image_ids:
            img_path = job.images.get(image_id)
            if img_path is None:
                raise HTTPException(400, f"Unknown image_id: {image_id}")
            with Image.open(img_path) as img:
                img.load()
                rgb = img.convert("RGB")
            crop = req.crops.get(image_id)
            if crop is not None:
                rgb = _apply_crop(rgb, crop)
            images.append(rgb)

        scales = [
            req.global_scale if req.global_scale is not None
            else req.scales.get(image_id, 1.0)
            for image_id in req.image_ids
        ]
        canvas_width_scale = (
            req.global_scale if req.global_scale is not None
            else max(scales, default=1.0)
        )

        try:
            canvas = build_canvas(images, scales, canvas_width_scale, show_grid=req.show_grid)
        except Exception as e:
            raise HTTPException(500, f"Layout failed: {e}")

        out_dir = STORAGE / job_id
        out_dir.mkdir(exist_ok=True)
        canvas_path = out_dir / "canvas.png"
        canvas.save(str(canvas_path), format="PNG", optimize=True)

        job.canvas_path = str(canvas_path)
        job.canvas_w, job.canvas_h = canvas.size
        job.status = "done"
        # Persist generate inputs so re-compose can replay them
        job.image_order = req.image_ids
        job.crops = req.crops
        job.scales = req.scales
        job.global_scale = req.global_scale
        job.show_grid = req.show_grid
        job.originals_expire_at = time.time() + ORIGINALS_TTL_SECONDS
        save_job(job)
    except Exception:
        job.status = "error"
        _cleanup_originals(job)
        raise

    return {"canvas_url": f"/jobs/{job_id}/canvas.png"}


@router.post("/jobs/{job_id}/recompose")
def recompose(job_id: str, req: RecomposeRequest):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if not job.images:
        raise HTTPException(410, "Originals have expired — start a new canvas")
    if not job.image_order:
        raise HTTPException(400, "No previous generate to replay")

    try:
        images: list[Image.Image] = []
        for image_id in job.image_order:
            img_path = job.images.get(image_id)
            if img_path is None:
                raise HTTPException(400, f"Image not found: {image_id}")
            with Image.open(img_path) as img:
                img.load()
                rgb = img.convert("RGB")
            crop = job.crops.get(image_id)
            if crop is not None:
                rgb = _apply_crop(rgb, crop)
            images.append(rgb)

        effective_global = req.global_scale if req.global_scale is not None else job.global_scale
        scales = [
            effective_global if effective_global is not None
            else job.scales.get(image_id, 1.0)
            for image_id in job.image_order
        ]
        canvas_width_scale = (
            effective_global if effective_global is not None
            else max(scales, default=1.0)
        )

        try:
            canvas = build_canvas(images, scales, canvas_width_scale, show_grid=req.show_grid)
        except Exception as e:
            raise HTTPException(500, f"Layout failed: {e}")

        out_dir = STORAGE / job_id
        out_dir.mkdir(exist_ok=True)
        canvas_path = out_dir / "canvas.png"
        canvas.save(str(canvas_path), format="PNG", optimize=True)

        job.canvas_path = str(canvas_path)
        job.canvas_w, job.canvas_h = canvas.size
        job.global_scale = effective_global
        job.show_grid = req.show_grid
        job.originals_expire_at = time.time() + ORIGINALS_TTL_SECONDS
        save_job(job)
    except Exception:
        raise

    return {"canvas_url": f"/jobs/{job_id}/canvas.png"}


@router.get("/jobs/{job_id}/canvas.png")
async def get_canvas(job_id: str):
    job = get_job(job_id)
    if job is None or job.canvas_path is None:
        raise HTTPException(404, "Canvas not found — run /generate first")
    return FileResponse(job.canvas_path, media_type="image/png")


@router.get("/jobs/{job_id}/original/{image_id}")
def get_original(job_id: str, image_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    img_path = job.images.get(image_id)
    if img_path is None:
        raise HTTPException(404, "Image not found")
    return FileResponse(img_path)


@router.get("/jobs/{job_id}/thumb/{image_id}")
def get_thumb(
    job_id: str,
    image_id: str,
    x: Optional[float] = Query(None, ge=0.0, le=1.0),
    y: Optional[float] = Query(None, ge=0.0, le=1.0),
    w: Optional[float] = Query(None, gt=0.0, le=1.0),
    h: Optional[float] = Query(None, gt=0.0, le=1.0),
):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    img_path = job.images.get(image_id)
    if img_path is None:
        raise HTTPException(404, "Image not found")

    buf = io.BytesIO()
    with Image.open(img_path) as img:
        img.load()
        rgb = img.convert("RGB")
        if None not in (x, y, w, h):
            rgb = _apply_crop(rgb, CropRect(x=x, y=y, w=w, h=h))
        rgb.thumbnail((256, 256))
        rgb.save(buf, format="JPEG", quality=80)
    return Response(content=buf.getvalue(), media_type="image/jpeg")
