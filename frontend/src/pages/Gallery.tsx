import { useEffect, useState } from "react";
import { getJobs, deleteJob, type JobRecord } from "../api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const CANVAS_URL = (jobId: string) => `${API_BASE}/jobs/${jobId}/canvas.png`;

export default function Gallery() {
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await getJobs();
        if (mounted) setJobs(data);
      } catch (e: unknown) {
        if (mounted) setError(String(e));
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await deleteJob(deletingId);
      setJobs((prev) => prev.filter((j) => j.job_id !== deletingId));
      setDeletingId(null);
    } catch (e: unknown) {
      setError(String(e));
      setDeletingId(null);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000)
      .toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
      .toUpperCase();
  };

  if (loading) return <p className="empty-hint">Consulting the archives...</p>;

  return (
    <section className="gallery">
      <div className="section-label">
        <span className="num">01 /</span>
        <h2>The Archives</h2>
        <span className="rule" />
      </div>

      {error && <div className="error">{error}</div>}

      {jobs.length === 0 ? (
        <p className="empty-hint">Your collection of reference sheets will appear here.</p>
      ) : (
        <div className="gallery-grid">
          {jobs.map((job, idx) => (
            <div key={job.job_id} className="gallery-item" style={{ animationDelay: `${idx * 50}ms` }}>
              <div className="gallery-thumb-wrap">
                <img
                  src={CANVAS_URL(job.job_id)}
                  alt={`Canvas ${job.job_id}`}
                  className="gallery-thumb"
                  onClick={() => setPreviewId(job.job_id)}
                />
                <div className="gallery-overlay">
                  <button className="preview-trigger" onClick={() => setPreviewId(job.job_id)}>
                    View Sheet
                  </button>
                </div>
              </div>
              <div className="gallery-meta">
                <span className="gallery-date">
                  {formatDate(job.created_at)}
                  {job.canvas_size && (
                    <span className="gallery-size">{job.canvas_size[0]} × {job.canvas_size[1]}</span>
                  )}
                </span>
                <div className="gallery-actions">
                  <a
                    href={CANVAS_URL(job.job_id)}
                    download={`reference-sheet-${job.job_id.slice(0, 8)}.png`}
                    className="gallery-action-btn"
                    title="Download PNG"
                  >
                    ↓
                  </a>
                  <button
                    className="gallery-action-btn delete"
                    onClick={() => setDeletingId(job.job_id)}
                    title="Delete permanently"
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {deletingId && (
        <div className="crop-dialog-backdrop" onMouseDown={() => setDeletingId(null)}>
          <div className="crop-dialog" style={{ width: "min(480px, 100%)" }} onMouseDown={(e) => e.stopPropagation()}>
            <header className="crop-dialog-header">
              <div>
                <div className="eyebrow">Irreversible Action</div>
                <h2>Delete Archive</h2>
              </div>
            </header>
            <div className="dialog-body">
              <p>
                Are you sure you want to delete this sheet? This will <strong>permanently remove</strong> the canvas and all its associated source references from the archive.
              </p>
            </div>
            <footer className="dialog-actions">
              <button className="ghost-btn" onClick={() => setDeletingId(null)}>
                Cancel
              </button>
              <button className="danger-btn" onClick={handleDelete}>
                Delete permanently
              </button>
            </footer>
          </div>
        </div>
      )}

      {previewId && (
        <div className="gallery-preview-backdrop" onClick={() => setPreviewId(null)}>
          <div className="gallery-preview-modal" onClick={(e) => e.stopPropagation()}>
            <div className="preview-modal-head">
              <span className="stamp">ARCHIVE № {previewId.slice(0, 8)}</span>
              <button className="close-preview" onClick={() => setPreviewId(null)}>×</button>
            </div>
            <div className="preview-modal-body">
              <img src={CANVAS_URL(previewId)} alt="Full Preview" />
            </div>
            <div className="preview-modal-foot">
              <a
                href={CANVAS_URL(previewId)}
                download={`reference-sheet-${previewId.slice(0, 8)}.png`}
                className="download-btn"
              >
                Download PNG
              </a>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
