from __future__ import annotations
import io
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response
from PIL import Image

from app.jobs import create_job, get_job, save_job
from app.models import GenerateRequest
from app.layout import build_canvas

router = APIRouter()

STORAGE = Path(__file__).parent.parent / "storage"
STORAGE.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_images(files: list[UploadFile] = File(...)):
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

    images: list[Image.Image] = []
    for image_id in req.image_ids:
        img_path = job.images.get(image_id)
        if img_path is None:
            raise HTTPException(400, f"Unknown image_id: {image_id}")
        with Image.open(img_path) as img:
            img.load()
            images.append(img.convert("RGB"))

    try:
        canvas = build_canvas(images)
    except Exception as e:
        raise HTTPException(500, f"Layout failed: {e}")

    out_dir = STORAGE / job_id
    out_dir.mkdir(exist_ok=True)
    canvas_path = out_dir / "canvas.png"
    canvas.save(str(canvas_path), format="PNG", optimize=True)

    job.canvas_path = str(canvas_path)
    job.status = "done"
    save_job(job)

    return {"canvas_url": f"/jobs/{job_id}/canvas.png"}


@router.get("/jobs/{job_id}/canvas.png")
async def get_canvas(job_id: str):
    job = get_job(job_id)
    if job is None or job.canvas_path is None:
        raise HTTPException(404, "Canvas not found — run /generate first")
    return FileResponse(job.canvas_path, media_type="image/png")


@router.get("/jobs/{job_id}/thumb/{image_id}")
def get_thumb(job_id: str, image_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    img_path = job.images.get(image_id)
    if img_path is None:
        raise HTTPException(404, "Image not found")

    buf = io.BytesIO()
    with Image.open(img_path) as img:
        img.thumbnail((256, 256))
        img.convert("RGB").save(buf, format="JPEG", quality=80)
    return Response(content=buf.getvalue(), media_type="image/jpeg")
