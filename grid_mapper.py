"""
Grid Mapper
- Detects grid lines on a warped Go board image
- Computes all 361 intersection points (19x19)
- Overlays them on the image for visual verification
- Saves the overlay as grid_overlay.jpg and intersection data as grid.npy
"""

import cv2
import numpy as np
import sys

BOARD_SIZE = 19

def find_grid_bounds(gray):
    """Find the bounding box of the grid by detecting lines."""
    # Threshold to find dark lines on light board
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Sum projections to find where lines cluster
    h_proj = np.sum(binary, axis=1)  # horizontal projection (rows)
    v_proj = np.sum(binary, axis=0)  # vertical projection (cols)

    # Find the region with significant line density
    h_thresh = np.max(h_proj) * 0.15
    v_thresh = np.max(v_proj) * 0.15

    h_lines = np.where(h_proj > h_thresh)[0]
    v_lines = np.where(v_proj > v_thresh)[0]

    top, bottom = h_lines[0], h_lines[-1]
    left, right = v_lines[0], v_lines[-1]

    return top, bottom, left, right

def compute_intersections(top, bottom, left, right):
    """Compute evenly spaced 19x19 intersection coordinates."""
    rows = np.linspace(top, bottom, BOARD_SIZE)
    cols = np.linspace(left, right, BOARD_SIZE)
    intersections = np.zeros((BOARD_SIZE, BOARD_SIZE, 2), dtype=np.float32)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            intersections[r, c] = [cols[c], rows[r]]  # (x, y)
    return intersections

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "warped_board.jpg"
    img = cv2.imread(path)
    if img is None:
        print(f"Could not load {path}")
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    top, bottom, left, right = find_grid_bounds(gray)
    print(f"Grid bounds: top={top}, bottom={bottom}, left={left}, right={right}")

    intersections = compute_intersections(top, bottom, left, right)

    # Draw overlay
    overlay = img.copy()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x, y = int(intersections[r, c, 0]), int(intersections[r, c, 1])
            cv2.circle(overlay, (x, y), 3, (0, 0, 255), -1)

    # Draw grid lines on overlay for reference
    for r in range(BOARD_SIZE):
        y = int(intersections[r, 0, 1])
        x0 = int(intersections[r, 0, 0])
        x1 = int(intersections[r, BOARD_SIZE - 1, 0])
        cv2.line(overlay, (x0, y), (x1, y), (0, 0, 255), 1)
    for c in range(BOARD_SIZE):
        x = int(intersections[0, c, 0])
        y0 = int(intersections[0, c, 1])
        y1 = int(intersections[BOARD_SIZE - 1, c, 1])
        cv2.line(overlay, (x, y0), (x, y1), (0, 0, 255), 1)

    cv2.imwrite("grid_overlay.jpg", overlay)
    np.save("grid.npy", intersections)
    print("Saved grid_overlay.jpg and grid.npy")

    cv2.imshow("Grid Overlay (press any key to close)", overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()