"""
Grid Mapper
- User clicks the 4 corner intersections of the grid (TL, TR, BR, BL)
- Computes all 361 intersection points (19x19) from those corners
- Overlays them on the image for visual verification
- Saves the overlay as grid_overlay.jpg and intersection data as grid.npy
"""

import cv2
import numpy as np
import sys

BOARD_SIZE = 19

def select_grid_corners(img):
    """Let the user click the 4 corner intersections of the grid."""
    corners = []
    h, w = img.shape[:2]
    scale = min(1.0, 700 / max(h, w))
    display = cv2.resize(img, (int(w * scale), int(h * scale)))

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(corners) < 4:
            corners.append((x, y))
            labels = ["TL", "TR", "BR", "BL"]
            print(f"  {labels[len(corners)-1]}: ({x}, {y})")

    win = "Click 4 grid corners: TL, TR, BR, BL (R=reset, Enter=confirm)"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_click)

    while True:
        vis = display.copy()
        labels = ["TL", "TR", "BR", "BL"]
        for i, pt in enumerate(corners):
            cv2.circle(vis, pt, 6, (0, 0, 255), -1)
            cv2.putText(vis, labels[i], (pt[0] + 10, pt[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        if len(corners) >= 2:
            for i in range(len(corners) - 1):
                cv2.line(vis, corners[i], corners[i + 1], (0, 255, 0), 1)
        if len(corners) == 4:
            cv2.line(vis, corners[3], corners[0], (0, 255, 0), 1)
        cv2.imshow(win, vis)
        key = cv2.waitKey(30) & 0xFF
        if key == 13 and len(corners) == 4:
            break
        elif key == ord('r'):
            corners.clear()
            print("  Corners reset")
        elif key == ord('q'):
            cv2.destroyAllWindows()
            sys.exit(0)

    cv2.destroyAllWindows()

    pts = np.array([(int(x / scale), int(y / scale)) for x, y in corners], dtype=np.float32)
    return pts  # TL, TR, BR, BL

def compute_intersections(corners):
    """Compute 19x19 intersections by interpolating between the 4 corners."""
    tl, tr, br, bl = corners

    intersections = np.zeros((BOARD_SIZE, BOARD_SIZE, 2), dtype=np.float32)
    for r in range(BOARD_SIZE):
        rt = r / (BOARD_SIZE - 1)
        left_pt = tl + rt * (bl - tl)
        right_pt = tr + rt * (br - tr)
        for c in range(BOARD_SIZE):
            ct = c / (BOARD_SIZE - 1)
            intersections[r, c] = left_pt + ct * (right_pt - left_pt)

    return intersections

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "warped_board.jpg"
    img = cv2.imread(path)
    if img is None:
        print(f"Could not load {path}")
        return

    print("Click the 4 corner INTERSECTIONS of the grid (not the board edges).")
    corners = select_grid_corners(img)
    intersections = compute_intersections(corners)

    # Draw overlay
    overlay = img.copy()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x, y = int(intersections[r, c, 0]), int(intersections[r, c, 1])
            cv2.circle(overlay, (x, y), 3, (0, 0, 255), -1)

    for r in range(BOARD_SIZE):
        x0, y0 = int(intersections[r, 0, 0]), int(intersections[r, 0, 1])
        x1, y1 = int(intersections[r, BOARD_SIZE - 1, 0]), int(intersections[r, BOARD_SIZE - 1, 1])
        cv2.line(overlay, (x0, y0), (x1, y1), (0, 0, 255), 1)
    for c in range(BOARD_SIZE):
        x0, y0 = int(intersections[0, c, 0]), int(intersections[0, c, 1])
        x1, y1 = int(intersections[BOARD_SIZE - 1, c, 0]), int(intersections[BOARD_SIZE - 1, c, 1])
        cv2.line(overlay, (x0, y0), (x1, y1), (0, 0, 255), 1)

    cv2.imwrite("grid_overlay.jpg", overlay)
    np.save("grid.npy", intersections)
    print("Saved grid_overlay.jpg and grid.npy")

    cv2.namedWindow("Grid Overlay (press any key to close)", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Grid Overlay (press any key to close)", 700, 700)
    cv2.imshow("Grid Overlay (press any key to close)", overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()