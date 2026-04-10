"""
Go Board Scanner Pipeline
- Live camera preview → capture photo
- Perspective warp the board
- Auto-generate grid (with manual override)
- Detect stones
- Export SGF + annotated image
"""

import cv2
import numpy as np
import sys
import time
from datetime import datetime

BOARD_SIZE = 19
OUTPUT_SIZE = 800
ROI_RADIUS = 12
PREVIEW_HEIGHT = 720


# ---------------------------------------------------------------------------
# 1. Capture
# ---------------------------------------------------------------------------

def capture_from_camera():
    """Live preview from Raspberry Pi camera; SPACE to capture, R to flip, Q to quit."""
    from picamera2 import Picamera2

    picam2 = Picamera2()
    full_res = picam2.sensor_resolution
    config = picam2.create_preview_configuration(
        main={"size": full_res, "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(1)

    flipped = False
    print(f"Capturing at {full_res[0]}x{full_res[1]}")
    print("SPACE = capture, R = flip 180°, Q = quit")

    frame = None
    while True:
        frame = picam2.capture_array()
        if flipped:
            frame = cv2.rotate(frame, cv2.ROTATE_180)

        h, w = frame.shape[:2]
        scale = PREVIEW_HEIGHT / h
        preview = cv2.resize(frame, (int(w * scale), PREVIEW_HEIGHT))
        cv2.imshow("Pi Camera Preview (SPACE=capture, R=flip, Q=quit)", preview)
        key = cv2.waitKey(1) & 0xFF

        if key == ord(" "):
            img_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            picam2.stop()
            cv2.destroyAllWindows()
            return img_bgr
        elif key == ord("r"):
            flipped = not flipped
            print(f"Rotation {'on' if flipped else 'off'}")
        elif key == ord("q"):
            picam2.stop()
            cv2.destroyAllWindows()
            sys.exit(0)


def capture_from_file(path):
    """Load an image file instead of using a camera."""
    img = cv2.imread(path)
    if img is None:
        print(f"Could not load {path}")
        sys.exit(1)
    return img


# ---------------------------------------------------------------------------
# 2. Warp board
# ---------------------------------------------------------------------------

def pick_corners(img, title, num=4):
    """Show image and let the user click `num` corners. Returns points in original coords."""
    corners = []
    h, w = img.shape[:2]
    scale = min(1.0, 1200 / max(h, w))
    display = cv2.resize(img, (int(w * scale), int(h * scale)))

    labels = ["TL", "TR", "BR", "BL"]

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(corners) < num:
            corners.append((x, y))
            print(f"  {labels[len(corners)-1]}: ({x}, {y})")

    win = f"{title} (R=reset, Enter=confirm, Q=quit)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, on_click)

    while True:
        vis = display.copy()
        for i, pt in enumerate(corners):
            cv2.circle(vis, pt, 6, (0, 0, 255), -1)
            cv2.putText(vis, labels[i], (pt[0] + 10, pt[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        if len(corners) >= 2:
            for i in range(len(corners) - 1):
                cv2.line(vis, corners[i], corners[i + 1], (0, 255, 0), 2)
        if len(corners) == 4:
            cv2.line(vis, corners[3], corners[0], (0, 255, 0), 2)
        cv2.imshow(win, vis)
        key = cv2.waitKey(30) & 0xFF
        if key == 13 and len(corners) == num:
            break
        elif key == ord("r"):
            corners.clear()
            print("  Corners reset")
        elif key == ord("q"):
            cv2.destroyAllWindows()
            sys.exit(0)

    cv2.destroyAllWindows()
    pts = np.array(
        [(int(x / scale), int(y / scale)) for x, y in corners], dtype=np.float32
    )
    return pts


def warp_board(img):
    """Prompt user to mark the 4 board corners, then warp to a square."""
    print("\n=== Step 2: Mark the 4 corners of the BOARD (TL, TR, BR, BL) ===")
    src = pick_corners(img, "Click 4 BOARD corners: TL, TR, BR, BL")
    dst = np.array(
        [[0, 0], [OUTPUT_SIZE, 0], [OUTPUT_SIZE, OUTPUT_SIZE], [0, OUTPUT_SIZE]],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (OUTPUT_SIZE, OUTPUT_SIZE))
    print("Board warped successfully.")
    return warped


# ---------------------------------------------------------------------------
# 3. Grid mapper
# ---------------------------------------------------------------------------

def compute_intersections(corners):
    """Bilinear interpolation of 19x19 intersections from 4 corner points."""
    tl, tr, br, bl = corners
    pts = np.zeros((BOARD_SIZE, BOARD_SIZE, 2), dtype=np.float32)
    for r in range(BOARD_SIZE):
        rt = r / (BOARD_SIZE - 1)
        left = tl + rt * (bl - tl)
        right = tr + rt * (br - tr)
        for c in range(BOARD_SIZE):
            ct = c / (BOARD_SIZE - 1)
            pts[r, c] = left + ct * (right - left)
    return pts


def auto_grid_corners(warped):
    """Estimate grid corners assuming the board edges have some margin."""
    h, w = warped.shape[:2]
    margin = int(min(h, w) * 0.03)
    tl = np.array([margin, margin], dtype=np.float32)
    tr = np.array([w - margin, margin], dtype=np.float32)
    br = np.array([w - margin, h - margin], dtype=np.float32)
    bl = np.array([margin, h - margin], dtype=np.float32)
    return np.array([tl, tr, br, bl])


def draw_grid_overlay(img, intersections):
    """Draw grid dots and lines on a copy of the image."""
    overlay = img.copy()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x, y = int(intersections[r, c, 0]), int(intersections[r, c, 1])
            cv2.circle(overlay, (x, y), 3, (0, 0, 255), -1)
    for r in range(BOARD_SIZE):
        p0 = tuple(intersections[r, 0].astype(int))
        p1 = tuple(intersections[r, BOARD_SIZE - 1].astype(int))
        cv2.line(overlay, p0, p1, (0, 0, 255), 1)
    for c in range(BOARD_SIZE):
        p0 = tuple(intersections[0, c].astype(int))
        p1 = tuple(intersections[BOARD_SIZE - 1, c].astype(int))
        cv2.line(overlay, p0, p1, (0, 0, 255), 1)
    return overlay


def map_grid(warped):
    """Auto-generate grid, show user, allow manual override."""
    print("\n=== Step 3: Grid mapping ===")
    corners = auto_grid_corners(warped)
    intersections = compute_intersections(corners)
    overlay = draw_grid_overlay(warped, intersections)

    win = "Auto grid — Y=accept, N=manual corners, Q=quit"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 700, 700)
    cv2.imshow(win, overlay)
    print("Review the auto-generated grid. Press Y to accept or N to set corners manually.")

    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord("y"):
            cv2.destroyAllWindows()
            print("Grid accepted.")
            return intersections
        elif key == ord("n"):
            cv2.destroyAllWindows()
            break
        elif key == ord("q"):
            cv2.destroyAllWindows()
            sys.exit(0)

    print("Mark the 4 corner INTERSECTIONS of the grid (TL, TR, BR, BL).")
    corners = pick_corners(warped, "Click 4 GRID corner intersections: TL, TR, BR, BL")
    intersections = compute_intersections(corners)

    overlay = draw_grid_overlay(warped, intersections)
    win2 = "Manual grid — press any key to continue"
    cv2.namedWindow(win2, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win2, 700, 700)
    cv2.imshow(win2, overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("Grid set manually.")
    return intersections


# ---------------------------------------------------------------------------
# 4. Detect stones
# ---------------------------------------------------------------------------

def classify_intersections(gray, intersections):
    """Classify each intersection as empty (0), black (1), or white (2)."""
    h, w = gray.shape
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
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

    median_val = np.median(means)
    median_std = np.median(stds)
    black_thresh = median_val - 40
    white_thresh = median_val + 20

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            uniform = stds[r, c] < median_std
            if means[r, c] < black_thresh and uniform:
                board[r, c] = 1
            elif means[r, c] > white_thresh and uniform:
                board[r, c] = 2
    return board


def draw_detections(img, intersections, board):
    """Draw detected stones on the image (blue=black stone, green=white stone)."""
    overlay = img.copy()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x, y = int(intersections[r, c, 0]), int(intersections[r, c, 1])
            if board[r, c] == 1:
                cv2.circle(overlay, (x, y), ROI_RADIUS, (255, 0, 0), 2)
                cv2.circle(overlay, (x, y), 2, (255, 0, 0), -1)
            elif board[r, c] == 2:
                cv2.circle(overlay, (x, y), ROI_RADIUS, (0, 255, 0), 2)
                cv2.circle(overlay, (x, y), 2, (0, 255, 0), -1)
    return overlay


def print_board(board):
    symbols = {0: ".", 1: "X", 2: "O"}
    col_labels = "A B C D E F G H J K L M N O P Q R S T"
    print(f"   {col_labels}")
    for r in range(BOARD_SIZE):
        row_num = BOARD_SIZE - r
        row_str = " ".join(symbols[board[r, c]] for c in range(BOARD_SIZE))
        print(f"{row_num:2d} {row_str} {row_num:2d}")
    print(f"   {col_labels}")


# ---------------------------------------------------------------------------
# 5. Export SGF
# ---------------------------------------------------------------------------

def board_to_sgf(board, filename):
    black, white = [], []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            coord = chr(ord("a") + c) + chr(ord("a") + r)
            if board[r, c] == 1:
                black.append(coord)
            elif board[r, c] == 2:
                white.append(coord)

    lines = [
        "(;",
        "GM[1]",
        "FF[4]",
        f"SZ[{BOARD_SIZE}]",
        f"DT[{datetime.now().strftime('%Y-%m-%d')}]",
        "AP[GoBoardScanner:1.0]",
        "CA[UTF-8]",
    ]
    if black:
        lines.append("AB" + "".join(f"[{s}]" for s in black))
    if white:
        lines.append("AW" + "".join(f"[{s}]" for s in white))
    lines.append(")")

    sgf_text = "\n".join(lines)
    with open(filename, "w") as f:
        f.write(sgf_text)
    print(f"Exported {len(black)} black and {len(white)} white stones → {filename}")
    return sgf_text


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    # --- Step 1: Capture ---
    print("=== Step 1: Capture ===")
    if len(sys.argv) > 1:
        img = capture_from_file(sys.argv[1])
        print(f"Loaded {sys.argv[1]}")
    else:
        try:
            img = capture_from_camera()
        except ImportError:
            print("picamera2 not available. Pass an image path as argument.")
            print("Usage: python go_camera.py [image.jpg]")
            sys.exit(1)

    # --- Step 2: Warp ---
    warped = warp_board(img)

    # --- Step 3: Grid ---
    intersections = map_grid(warped)

    # --- Step 4: Detect ---
    print("\n=== Step 4: Stone detection ===")
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    board = classify_intersections(gray, intersections)
    print_board(board)

    # --- Step 5: Export ---
    print("\n=== Step 5: Export ===")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    sgf_file = f"go_scan_{timestamp}.sgf"
    board_to_sgf(board, sgf_file)

    # Combined overlay: grid + detections
    overlay = draw_grid_overlay(warped, intersections)
    overlay = draw_detections(overlay, intersections, board)
    overlay_file = f"go_scan_{timestamp}.jpg"
    cv2.imwrite(overlay_file, overlay)
    print(f"Saved annotated board → {overlay_file}")

    # Show final result
    win = "Final result (press any key to close)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 700, 700)
    cv2.imshow(win, overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("\nDone!")


if __name__ == "__main__":
    main()