from __future__ import annotations
from PIL import Image

CELL_HEIGHT = 800          # px — reference image height at scale 1×
REF_EXTRA_BELOW = 0.5      # blank space below reference, as a fraction of the cell height
DRAW_SCALE = 1.5           # drawing cell is this multiple of the reference (W and H)
PAIR_GAP = 80              # gap between reference and drawing block
COL_GAP = 200              # gap between the two pair columns
ROW_GAP = 320              # vertical gap between rows
OUTER_PAD = 80             # canvas outer margin
CANVAS_WIDTH = 4000        # fixed canvas width; height scales with rows
N_COLS = 2                 # number of ref+draw pairs per row


def _fit_to_height(img: Image.Image, target_h: int) -> Image.Image:
    w, h = img.size
    new_w = max(1, int(w * target_h / h))
    return img.resize((new_w, target_h), Image.LANCZOS)


def build_canvas(
    images: list[Image.Image],
    scales: list[float] | None = None,
    canvas_width_scale: float = 1.0,
) -> Image.Image:
    """
    2-column grid. Each cell = reference block (image + 0.5× blank below)
    alongside a drawing block sized 1.5× the reference in both dimensions.

    `scales[i]` is a per-image multiplier applied to CELL_HEIGHT; the drawing
    block grows proportionally because it is derived from the reference's
    rendered width.
    """
    canvas_width = max(1, int(CANVAS_WIDTH * canvas_width_scale))

    if not images:
        return Image.new("RGB", (canvas_width, canvas_width), "white")

    if scales is None or len(scales) != len(images):
        scales = [1.0] * len(images)

    target_hs = [max(1, int(CELL_HEIGHT * s)) for s in scales]
    fitted = [_fit_to_height(img, h) for img, h in zip(images, target_hs)]

    ref_ws = [f.width for f in fitted]
    draw_ws = [int(rw * DRAW_SCALE) for rw in ref_ws]
    draw_hs = [int(h * DRAW_SCALE) for h in target_hs]
    ref_block_hs = [int(h * (1 + REF_EXTRA_BELOW)) for h in target_hs]
    pair_ws = [rw + PAIR_GAP + dw for rw, dw in zip(ref_ws, draw_ws)]
    pair_hs = [max(rb, dh) for rb, dh in zip(ref_block_hs, draw_hs)]

    row_indices: list[list[int]] = [
        list(range(i, min(i + N_COLS, len(images))))
        for i in range(0, len(images), N_COLS)
    ]

    # Single slot width across the whole canvas keeps columns aligned.
    row_pair_w_max = max(pair_ws[i] for row in row_indices for i in row)
    row_hs = [max(pair_hs[i] for i in row) for row in row_indices]

    natural_w = OUTER_PAD * 2 + row_pair_w_max * N_COLS + COL_GAP * (N_COLS - 1)
    natural_h = OUTER_PAD * 2 + sum(row_hs) + ROW_GAP * (len(row_indices) - 1)

    scale = canvas_width / natural_w
    canvas_w = canvas_width
    canvas_h = int(natural_h * scale)

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")

    scaled_col_gap = int(COL_GAP * scale)
    scaled_row_gap = int(ROW_GAP * scale)
    scaled_slot_w = int(row_pair_w_max * scale)
    pad = int(OUTER_PAD * scale)

    y = pad
    for r, row in enumerate(row_indices):
        for col_idx, i in enumerate(row):
            slot_x = pad + col_idx * (scaled_slot_w + scaled_col_gap)
            scaled_cell_h = max(1, int(target_hs[i] * scale))
            scaled_img = _fit_to_height(fitted[i], scaled_cell_h)
            canvas.paste(scaled_img, (slot_x, y))
        y += int(row_hs[r] * scale) + scaled_row_gap

    return canvas
