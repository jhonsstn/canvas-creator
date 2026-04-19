import { useCallback, useEffect, useState } from "react";
import Cropper from "react-easy-crop";
import type { Area } from "react-easy-crop";
import type { CropRect } from "./api";

type AspectOption = "free" | "1:1" | "3:4";

const ASPECT_VALUES: Record<AspectOption, number | undefined> = {
  free: undefined,
  "1:1": 1,
  "3:4": 3 / 4,
};

interface Props {
  imageUrl: string;
  filename: string;
  indexLabel: string;
  initialCrop?: CropRect;
  onSave: (crop: CropRect | null) => void;
  onClose: () => void;
}

export default function CropDialog({
  imageUrl,
  filename,
  indexLabel,
  initialCrop,
  onSave,
  onClose,
}: Props) {
  const [aspect, setAspect] = useState<AspectOption>("free");
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [areaPixels, setAreaPixels] = useState<Area | null>(null);
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);

  useEffect(() => {
    const img = new Image();
    img.onload = () => setNatural({ w: img.naturalWidth, h: img.naturalHeight });
    img.src = imageUrl;
  }, [imageUrl]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const onCropComplete = useCallback(
    (_area: Area, pixels: Area) => setAreaPixels(pixels),
    []
  );

  const initialAreaPixels: Area | undefined =
    initialCrop && natural
      ? {
          x: initialCrop.x * natural.w,
          y: initialCrop.y * natural.h,
          width: initialCrop.w * natural.w,
          height: initialCrop.h * natural.h,
        }
      : undefined;

  const handleSave = () => {
    if (!areaPixels || !natural) return;
    const rect: CropRect = {
      x: Math.max(0, areaPixels.x / natural.w),
      y: Math.max(0, areaPixels.y / natural.h),
      w: Math.min(1, areaPixels.width / natural.w),
      h: Math.min(1, areaPixels.height / natural.h),
    };
    onSave(rect);
  };

  return (
    <div className="crop-dialog-backdrop" onMouseDown={onClose}>
      <div className="crop-dialog" onMouseDown={(e) => e.stopPropagation()}>
        <header className="crop-dialog-header">
          <div>
            <div className="eyebrow">Crop · {indexLabel}</div>
            <h2>Frame the reference</h2>
          </div>
          <span className="crop-filename" title={filename}>
            {filename}
          </span>
        </header>

        <div className="aspect-radios" role="radiogroup" aria-label="Aspect ratio">
          {(Object.keys(ASPECT_VALUES) as AspectOption[]).map((opt) => (
            <button
              key={opt}
              role="radio"
              aria-checked={aspect === opt}
              className={`aspect-radio${aspect === opt ? " selected" : ""}`}
              onClick={() => setAspect(opt)}
              type="button"
            >
              {opt === "free" ? "Free" : opt}
            </button>
          ))}
        </div>

        <div className="crop-area">
          <Cropper
            image={imageUrl}
            crop={crop}
            zoom={zoom}
            aspect={ASPECT_VALUES[aspect]}
            onCropChange={setCrop}
            onZoomChange={setZoom}
            onCropComplete={onCropComplete}
            initialCroppedAreaPixels={initialAreaPixels}
            restrictPosition={true}
            objectFit="contain"
            classes={{
              containerClassName: "rec-container",
              mediaClassName: "rec-media",
              cropAreaClassName: "rec-area",
            }}
          />
        </div>

        <footer className="crop-actions">
          <button className="link-btn" type="button" onClick={() => onSave(null)}>
            Reset
          </button>
          <button className="ghost-btn" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="generate-btn" type="button" onClick={handleSave}>
            Save crop
          </button>
        </footer>
      </div>
    </div>
  );
}
