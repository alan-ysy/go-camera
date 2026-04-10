"""Quick debug: print mean/std at problem intersections."""
import cv2
import numpy as np
import sys

ROI_RADIUS = 12
BOARD_SIZE = 19

# SGF-style column mapping (no I)
COLS = "ABCDEFGHJKLMNOPQRST"

def coord_to_index(col_letter, row_num):
    """Convert e.g. ('C', 16) to grid indices (r, c)."""
    c = COLS.index(col_letter)
    r = BOARD_SIZE - row_num
    return r, c

img_path = sys.argv[1] if len(sys.argv) > 1 else "warped_board.jpg"
grid_path = sys.argv[2] if len(sys.argv) > 2 else "grid.npy"

gray = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2GRAY)
intersections = np.load(grid_path)
h, w = gray.shape

# Collect all stats
means = np.zeros((BOARD_SIZE, BOARD_SIZE))
stds = np.zeros((BOARD_SIZE, BOARD_SIZE))
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        x, y = int(intersections[r, c, 0]), int(intersections[r, c, 1])
        y0, y1 = max(0, y - ROI_RADIUS), min(h, y + ROI_RADIUS)
        x0, x1 = max(0, x - ROI_RADIUS), min(w, x + ROI_RADIUS)
        roi = gray[y0:y1, x0:x1]
        means[r, c] = np.mean(roi)
        stds[r, c] = np.std(roi)

median_mean = np.median(means)
median_std = np.median(stds)
print(f"Board median brightness: {median_mean:.1f}")
print(f"Board median std:        {median_std:.1f}")
print()

# Check specific spots
spots = [
    ("C", 16, "missed white"),
    ("P", 17, "detected white"),
    ("Q", 17, "detected white"),
    ("D", 10, "detected white"),
    ("J", 4,  "detected black (center fold)"),
    ("N", 1,  "false positive white"),
    ("D", 3,  "detected white"),
    ("E", 5,  "empty (for reference)"),
]

print(f"{'Spot':<8} {'Expected':<22} {'Mean':>6} {'Std':>6} {'M-med':>7} {'Uniform':>8}")
print("-" * 60)
for col, row, label in spots:
    r, c = coord_to_index(col, row)
    m, s = means[r, c], stds[r, c]
    print(f"{col}{row:<4}    {label:<22} {m:6.1f} {s:6.1f} {m - median_mean:+7.1f} {'yes' if s < median_std else 'no':>8}")