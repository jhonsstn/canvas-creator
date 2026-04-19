const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface UploadedImage {
  image_id: string;
  filename: string;
  job_id: string;
}

export interface UploadResponse {
  job_id: string;
  images: UploadedImage[];
}

export interface CropRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export async function uploadImages(files: File[]): Promise<UploadResponse> {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generateCanvas(
  jobId: string,
  imageIds: string[],
  crops: Record<string, CropRect> = {}
): Promise<string> {
  const res = await fetch(`${BASE}/jobs/${jobId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_ids: imageIds, crops }),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return `${BASE}${data.canvas_url}`;
}

export function thumbUrl(
  jobId: string,
  imageId: string,
  crop?: CropRect
): string {
  const base = `${BASE}/jobs/${jobId}/thumb/${imageId}`;
  if (!crop) return base;
  const q = new URLSearchParams({
    x: String(crop.x),
    y: String(crop.y),
    w: String(crop.w),
    h: String(crop.h),
  });
  return `${base}?${q.toString()}`;
}
