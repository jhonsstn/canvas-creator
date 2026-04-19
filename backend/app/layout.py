from __future__ import annotations
from PIL import Image

CELL_HEIGHT = 800          # px — each image/drawing cell height
COL_GAP = 200              # horizontal gap between image and drawing cell
ROW_GAP = 160              # vertical gap between rows
OUTER_PAD = 80             # canvas outer margin
MIN_CANVAS_SIZE = 4000     # enforce at least 4000x4000


def _fit_to_height(img: Image.Image, target_h: int) -> Image.Image:
    w, h = img.size
    new_w = max(1, int(w * target_h / h))
    return img.resize((new_w, target_h), Image.LANCZOS)


def build_canvas(images: list[Image.Image]) -> Image.Image:
    """
    Lay out each reference image in the left column with an equal-sized
    blank white drawing cell to its right.
    """
    if not images:
        return Image.new("RGB", (MIN_CANVAS_SIZE, MIN_CANVAS_SIZE), "white")

    fitted = [_fit_to_height(img, CELL_HEIGHT) for img in images]
    max_w = max(img.width for img in fitted)

    canvas_w = OUTER_PAD * 2 + max_w * 2 + COL_GAP
    canvas_h = OUTER_PAD * 2 + len(fitted) * CELL_HEIGHT + ROW_GAP * (len(fitted) - 1)

    scale = 1.0
    if canvas_w < MIN_CANVAS_SIZE or canvas_h < MIN_CANVAS_SIZE:
        scale = max(MIN_CANVAS_SIZE / canvas_w, MIN_CANVAS_SIZE / canvas_h)
        canvas_w = int(canvas_w * scale)
        canvas_h = int(canvas_h * scale)

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")

    scaled_cell_h = int(CELL_HEIGHT * scale)
    scaled_row_gap = int(ROW_GAP * scale)
    scaled_col_gap = int(COL_GAP * scale)
    scaled_max_w = int(max_w * scale)
    pad = int(OUTER_PAD * scale)

    y = pad
    for img in fitted:
        scaled_img = _fit_to_height(img, scaled_cell_h)
        # Left column: the reference image, left-aligned within the cell
        canvas.paste(scaled_img, (pad, y))
        # Right column: blank white cell (canvas is already white — nothing to paint)
        # Advance y past this row
        y += scaled_cell_h + scaled_row_gap

    return canvas
