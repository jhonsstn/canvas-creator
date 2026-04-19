import { useCallback, useRef, useState } from "react";
import type { CropRect, UploadedImage } from "../api";
import { generateCanvas, thumbUrl, uploadImages } from "../api";
import CropDialog from "../CropDialog";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const ORIGINAL_URL = (jobId: string, imageId: string) =>
  `${API_BASE}/jobs/${jobId}/original/${imageId}`;

const TODAY = new Date()
  .toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
  .toUpperCase();

export default function Creator() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [rows, setRows] = useState<UploadedImage[]>([]);
  const [crops, setCrops] = useState<Record<string, CropRect>>({});
  const [editing, setEditing] = useState<{ row: UploadedImage; index: number } | null>(null);
  const [canvasUrl, setCanvasUrl] = useState<string | null>(null);
  const [canvasSize, setCanvasSize] = useState<{ w: number; h: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    const fileArr = Array.from(files).filter((f) => f.type.startsWith("image/"));
    if (!fileArr.length) return;
    setLoading(true);
    setError(null);
    try {
      const res = await uploadImages(fileArr);
      setJobId(res.job_id);
      setRows((prev) => [...prev, ...res.images]);
      setCanvasUrl(null);
      setCanvasSize(null);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) handleFiles(e.target.files);
    },
    [handleFiles]
  );

  const removeRow = (id: string) => {
    setRows((prev) => prev.filter((r) => r.image_id !== id));
    setCrops((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const handleGenerate = async () => {
    if (!jobId || rows.length === 0) return;
    setLoading(true);
    setError(null);
    setCanvasUrl(null);
    try {
      const url = await generateCanvas(
        jobId,
        rows.map((r) => r.image_id),
        crops
      );
      setCanvasUrl(url + "?t=" + Date.now());
      setRows([]);
      setCrops({});
      setJobId(null);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCrop = (crop: CropRect | null) => {
    if (!editing) return;
    const id = editing.row.image_id;
    setCrops((prev) => {
      const next = { ...prev };
      if (crop) next[id] = crop;
      else delete next[id];
      return next;
    });
    setEditing(null);
  };

  const count = rows.length;

  return (
    <>
      <section>
        <div className="section-label">
          <span className="num">01 /</span>
          <h2>Upload references</h2>
          <span className="rule" />
        </div>

        <div
          ref={dropRef}
          className={`dropzone${loading ? " disabled" : ""}`}
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => document.getElementById("file-input")?.click()}
        >
          <span className="plus">+</span>
          <span className="primary">Drop images · or click to browse</span>
          <span className="secondary">PNG, JPG, WebP — any size, any shape</span>
          <input
            id="file-input"
            type="file"
            multiple
            accept="image/*"
            style={{ display: "none" }}
            onChange={onInputChange}
          />
        </div>
      </section>

      {rows.length > 0 && (
        <section className="image-list">
          <div className="section-label">
            <span className="num">02 /</span>
            <h2>Plates</h2>
            <span className="rule" />
          </div>

          <div className="plates">
            {rows.map((row, idx) => {
              const crop = crops[row.image_id];
              return (
                <div key={row.image_id} className="plate" style={{ animationDelay: `${idx * 40}ms` }}>
                  <span className="plate-index">№ {String(idx + 1).padStart(2, "0")}</span>
                  <button
                    type="button"
                    className="thumb-btn"
                    onClick={() => setEditing({ row, index: idx + 1 })}
                    aria-label="Edit crop"
                  >
                    <img
                      src={thumbUrl(row.job_id, row.image_id, crop)}
                      alt={row.filename}
                      className="thumb"
                    />
                    <span className="thumb-hint">Click · Crop</span>
                  </button>
                  <div className="plate-foot">
                    <span className="filename" title={row.filename}>{row.filename}</span>
                    {crop && <span className="plate-badge">Cropped</span>}
                    <button
                      className="remove-btn"
                      onClick={() => removeRow(row.image_id)}
                      aria-label="Remove"
                    >
                      ×
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="generate-bar">
            <span className="hint">
              Each reference will be paired with a blank drawing cell.
            </span>
            <button
              className="generate-btn"
              onClick={handleGenerate}
              disabled={loading}
            >
              {loading ? "Composing" : "Compose canvas"}
            </button>
          </div>
        </section>
      )}

      {error && <div className="error">{error}</div>}

      {canvasUrl && (
        <section className="preview">
          <div className="preview-head">
            <div>
              <div className="eyebrow">Result</div>
              <h2>The finished sheet</h2>
            </div>
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
              <span className="stamp">№ {String(count).padStart(2, "0")} · {TODAY}</span>
              {canvasSize && (
                <span className="stamp dims-stamp">
                  {canvasSize.w.toLocaleString()} × {canvasSize.h.toLocaleString()} px
                </span>
              )}
              <a href={canvasUrl} download="reference-canvas.png" className="download-btn">
                Download PNG
              </a>
            </div>
          </div>
          <div className="canvas-frame">
            <img
              src={canvasUrl}
              alt="Generated reference canvas"
              className="canvas-preview"
              onLoad={(e) => {
                const el = e.currentTarget;
                setCanvasSize({ w: el.naturalWidth, h: el.naturalHeight });
              }}
            />
          </div>
          <p className="caption">Reference sheet, composed {TODAY.toLowerCase()}.</p>
        </section>
      )}

      {editing && (
        <CropDialog
          imageUrl={ORIGINAL_URL(editing.row.job_id, editing.row.image_id)}
          filename={editing.row.filename}
          indexLabel={`№ ${String(editing.index).padStart(2, "0")}`}
          initialCrop={crops[editing.row.image_id]}
          onSave={handleSaveCrop}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}
