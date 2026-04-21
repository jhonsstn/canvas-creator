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

export const SCALE_PRESETS = [0.75, 1, 1.5, 2, 2.5, 3] as const;
export type ScalePreset = (typeof SCALE_PRESETS)[number];

export async function generateCanvas(
  jobId: string,
  imageIds: string[],
  crops: Record<string, CropRect> = {},
  scales: Record<string, number> = {},
  globalScale: number | null = null,
  showGrid: boolean = false
): Promise<string> {
  const body: Record<string, unknown> = {
    image_ids: imageIds,
    crops,
    scales,
  };
  if (globalScale !== null) body.global_scale = globalScale;
  if (showGrid) body.show_grid = true;
  const res = await fetch(`${BASE}/jobs/${jobId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return `${BASE}${data.canvas_url}`;
}

export interface JobRecord {
  job_id: string;
  created_at: number;
  status: string;
  has_canvas: boolean;
  canvas_size: [number, number] | null;
}

export async function getJobs(): Promise<JobRecord[]> {
  const res = await fetch(`${BASE}/jobs`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(4000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function deleteJob(jobId: string): Promise<void> {
  const res = await fetch(`${BASE}/jobs/${jobId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
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
