import { useCallback, useRef, useState } from "react";
import type { UploadedImage } from "./api";
import { generateCanvas, thumbUrl, uploadImages } from "./api";
import "./App.css";

const TODAY = new Date().toLocaleDateString("en-GB", {
  day: "2-digit",
  month: "short",
  year: "numeric",
}).toUpperCase();

export default function App() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [rows, setRows] = useState<UploadedImage[]>([]);
  const [canvasUrl, setCanvasUrl] = useState<string | null>(null);
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
  };

  const handleGenerate = async () => {
    if (!jobId || rows.length === 0) return;
    setLoading(true);
    setError(null);
    setCanvasUrl(null);
    try {
      const url = await generateCanvas(jobId, rows.map((r) => r.image_id));
      setCanvasUrl(url + "?t=" + Date.now());
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const count = rows.length;
  const plural = count === 1 ? "plate" : "plates";

  return (
    <div className="app">
      <header>
        <div>
          <div className="eyebrow">Atelier №01 · Reference Sheets</div>
          <h1>
            Canvas <em>Creator</em>
          </h1>
          <p className="subtitle">
            A quiet little workbench for arranging references
            onto a single drawing sheet.
          </p>
        </div>
        <div className="meta">
          <div><strong>{TODAY}</strong></div>
          <div>{String(count).padStart(2, "0")} {plural}</div>
          <div>{canvasUrl ? "CANVAS · READY" : "CANVAS · AWAITING"}</div>
        </div>
      </header>

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
            {rows.map((row, idx) => (
              <div key={row.image_id} className="plate" style={{ animationDelay: `${idx * 40}ms` }}>
                <span className="plate-index">№ {String(idx + 1).padStart(2, "0")}</span>
                <div className="thumb-wrap">
                  <img
                    src={thumbUrl(row.job_id, row.image_id)}
                    alt={row.filename}
                    className="thumb"
                  />
                </div>
                <div className="plate-foot">
                  <span className="filename" title={row.filename}>{row.filename}</span>
                  <button
                    className="remove-btn"
                    onClick={() => removeRow(row.image_id)}
                    aria-label="Remove"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
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
              <a href={canvasUrl} download="reference-canvas.png" className="download-btn">
                Download PNG
              </a>
            </div>
          </div>
          <div className="canvas-frame">
            <img src={canvasUrl} alt="Generated reference canvas" className="canvas-preview" />
          </div>
          <p className="caption">Reference sheet, composed {TODAY.toLowerCase()}.</p>
        </section>
      )}
    </div>
  );
}
