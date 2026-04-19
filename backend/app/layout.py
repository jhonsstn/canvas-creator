from __future__ import annotations
from PIL import Image

CELL_HEIGHT = 800          # px — reference image height
REF_EXTRA_BELOW = 0.5      # blank space below reference, as a fraction of CELL_HEIGHT
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


def build_canvas(images: list[Image.Image]) -> Image.Image:
    """
    2-column grid. Each cell = reference block (image + 0.5× blank below)
    alongside a drawing block sized 1.5× the reference in both dimensions.

    Row layout: [ ref | draw(1.5×) || ref | draw(1.5×) ]
    """
    if not images:
        return Image.new("RGB", (CANVAS_WIDTH, CANVAS_WIDTH), "white")

    fitted = [_fit_to_height(img, CELL_HEIGHT) for img in images]

    rows: list[list[Image.Image]] = [
        fitted[i:i + N_COLS] for i in range(0, len(fitted), N_COLS)
    ]

    # Uniform ref-block width: widest reference across all rows.
    ref_w = max(img.width for img in fitted)
    ref_block_h = int(CELL_HEIGHT * (1 + REF_EXTRA_BELOW))
    draw_w = int(ref_w * DRAW_SCALE)
    draw_h = int(CELL_HEIGHT * DRAW_SCALE)

    pair_w = ref_w + PAIR_GAP + draw_w
    row_h = max(ref_block_h, draw_h)

    natural_w = OUTER_PAD * 2 + pair_w * N_COLS + COL_GAP * (N_COLS - 1)
    natural_h = OUTER_PAD * 2 + len(rows) * row_h + ROW_GAP * (len(rows) - 1)

    scale = CANVAS_WIDTH / natural_w
    canvas_w = CANVAS_WIDTH
    canvas_h = int(natural_h * scale)

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")

    scaled_cell_h = int(CELL_HEIGHT * scale)
    scaled_ref_w = int(ref_w * scale)
    scaled_pair_gap = int(PAIR_GAP * scale)
    scaled_pair_w = int(pair_w * scale)
    scaled_row_h = int(row_h * scale)
    scaled_row_gap = int(ROW_GAP * scale)
    scaled_col_gap = int(COL_GAP * scale)
    pad = int(OUTER_PAD * scale)

    y = pad
    for row in rows:
        for col_idx, img in enumerate(row):
            pair_x = pad + col_idx * (scaled_pair_w + scaled_col_gap)
            scaled_img = _fit_to_height(img, scaled_cell_h)
            # Reference sits at the top-left of the pair, horizontally centered
            # within the uniform ref width so narrower images don't shift.
            img_x = pair_x + (scaled_ref_w - scaled_img.width) // 2
            canvas.paste(scaled_img, (img_x, y))
            # Blank below reference and the drawing block are already white.
        y += scaled_row_h + scaled_row_gap

    return canvas
