from __future__ import annotations
from PIL import Image

CELL_HEIGHT = 800          # px — each image/drawing cell height
PAIR_GAP = 80              # gap between an image and its drawing blank
COL_GAP = 200              # gap between the two image+blank columns
ROW_GAP = 320              # vertical gap between rows
OUTER_PAD = 80             # canvas outer margin
MIN_CANVAS_SIZE = 4000     # enforce at least 4000x4000
N_COLS = 2                 # number of image+blank pairs per row


def _fit_to_height(img: Image.Image, target_h: int) -> Image.Image:
    w, h = img.size
    new_w = max(1, int(w * target_h / h))
    return img.resize((new_w, target_h), Image.LANCZOS)


def build_canvas(images: list[Image.Image]) -> Image.Image:
    """
    2-column grid. Each cell is a reference image paired with an
    equal-sized blank drawing cell to its right.
    Row layout: [ img | blank || img | blank ]
    """
    if not images:
        return Image.new("RGB", (MIN_CANVAS_SIZE, MIN_CANVAS_SIZE), "white")

    fitted = [_fit_to_height(img, CELL_HEIGHT) for img in images]

    rows: list[list[Image.Image]] = [
        fitted[i:i + N_COLS] for i in range(0, len(fitted), N_COLS)
    ]

    # Uniform pair width: widest image determines image & blank width.
    pair_img_w = max(img.width for img in fitted)
    pair_w = pair_img_w * 2 + PAIR_GAP

    canvas_w = OUTER_PAD * 2 + pair_w * N_COLS + COL_GAP * (N_COLS - 1)
    canvas_h = OUTER_PAD * 2 + len(rows) * CELL_HEIGHT + ROW_GAP * (len(rows) - 1)

    scale = 1.0
    if canvas_w < MIN_CANVAS_SIZE or canvas_h < MIN_CANVAS_SIZE:
        scale = max(MIN_CANVAS_SIZE / canvas_w, MIN_CANVAS_SIZE / canvas_h)
        canvas_w = int(canvas_w * scale)
        canvas_h = int(canvas_h * scale)

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")

    scaled_cell_h = int(CELL_HEIGHT * scale)
    scaled_row_gap = int(ROW_GAP * scale)
    scaled_col_gap = int(COL_GAP * scale)
    scaled_pair_gap = int(PAIR_GAP * scale)
    scaled_pair_img_w = int(pair_img_w * scale)
    scaled_pair_w = scaled_pair_img_w * 2 + scaled_pair_gap
    pad = int(OUTER_PAD * scale)

    y = pad
    for row in rows:
        for col_idx, img in enumerate(row):
            pair_x = pad + col_idx * (scaled_pair_w + scaled_col_gap)
            scaled_img = _fit_to_height(img, scaled_cell_h)
            # Center the image within its image-half of the pair
            img_x = pair_x + (scaled_pair_img_w - scaled_img.width) // 2
            canvas.paste(scaled_img, (img_x, y))
            # Blank half to the right is already white — nothing to paint
        y += scaled_cell_h + scaled_row_gap

    return canvas
