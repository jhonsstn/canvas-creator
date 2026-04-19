const BASE = "http://localhost:8000";

export interface UploadedImage {
  image_id: string;
  filename: string;
  job_id: string;
}

export interface UploadResponse {
  job_id: string;
  images: UploadedImage[];
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
  imageIds: string[]
): Promise<string> {
  const res = await fetch(`${BASE}/jobs/${jobId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_ids: imageIds }),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return `${BASE}${data.canvas_url}`;
}

export function thumbUrl(jobId: string, imageId: string): string {
  return `${BASE}/jobs/${jobId}/thumb/${imageId}`;
}
