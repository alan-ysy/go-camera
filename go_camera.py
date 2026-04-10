"""
Go Board Vision Pipeline
Load image → select corners → warp → detect grid → classify stones → export SGF
"""

import cv2
import numpy as np
import sys
import os
import time
from datetime import datetime

# === Config ===
BOARD_SIZE = 19
OUTPUT_SIZE = 800
ROI_RADIUS = 12

# === Step 1: Load Image ===
def load_image(path):
    img = cv2.imread(path)
    if img is None:
        print(f"Could not load {path}")
        sys.exit(1)
    return img

# === Step 2: Manual Corner Selection & Perspective Warp ===
def select_corners(img):
    corners = []
    h, w = img.shape[:2]
    scale = min(1.0, 1200 / max(h, w))
    display = cv2.resize(img, (int(w * scale), int(h * scale)))

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(corners) < 4:
            corners.append((x, y))
            print(f"  Corner {len(corners)}: ({x}, {y})")

    win = "Select 4 corners: TL, TR, BR, BL (R=reset, Enter=confirm)"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_click)

    while True:
        vis = display.copy()
        for i, pt in enumerate(corners):
            cv2.circle(vis, pt, 6, (0, 0, 255), -1)
            cv2.putText(vis, str(i + 1), (pt[0] + 10, pt[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        if len(corners) >= 2:
            for i in range(len(corners) - 1):
                cv2.line(vis, corners[i], corners[i + 1], (0, 255, 0), 2)
        if len(corners) == 4:
            cv2.line(vis, corners[3], corners[0], (0, 255, 0), 2)
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
    src = np.array([(int(x / scale), int(y / scale)) for x, y in corners], dtype=np.float32)
    return src

def warp_board(img, src_corners):
    dst = np.array([
        [0, 0], [OUTPUT_SIZE, 0],
        [OUTPUT_SIZE, OUTPUT_SIZE], [0, OUTPUT_SIZE]
    ], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_corners, dst)
    return cv2.warpPerspective(img, M, (OUTPUT_SIZE, OUTPUT_SIZE))

# === Step 3: Grid Detection ===
def find_grid(gray):
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    h_proj = np.sum(binary, axis=1)
    v_proj = np.sum(binary, axis=0)
    h_lines = np.where(h_proj > np.max(h_proj) * 0.15)[0]
    v_lines = np.where(v_proj > np.max(v_proj) * 0.15)[0]
    top, bottom = h_lines[0], h_lines[-1]
    left, right = v_lines[0], v_lines[-1]

    rows = np.linspace(top, bottom, BOARD_SIZE)
    cols = np.linspace(left, right, BOARD_SIZE)
    intersections = np.zeros((BOARD_SIZE, BOARD_SIZE, 2), dtype=np.float32)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            intersections[r, c] = [cols[c], rows[r]]
    return intersections

# === Step 4: Stone Detection ===
def detect_stones(gray, intersections):
    h, w = gray.shape
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

    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            is_uniform = stds[r, c] < median_std
            if means[r, c] < median_val - 40 and is_uniform:
                board[r, c] = 1  # black
            elif means[r, c] > median_val + 20 and is_uniform:
                board[r, c] = 2  # white
    return board

# === Step 5: SGF Export ===
def export_sgf(board, filename):
    black, white = [], []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            coord = chr(ord('a') + c) + chr(ord('a') + r)
            if board[r, c] == 1:
                black.append(coord)
            elif board[r, c] == 2:
                white.append(coord)

    lines = [
        "(;", "GM[1]", "FF[4]", f"SZ[{BOARD_SIZE}]",
        f"DT[{datetime.now().strftime('%Y-%m-%d')}]",
        "AP[GoBoardVision:1.0]", "CA[UTF-8]",
    ]
    if black:
        lines.append("AB" + "".join(f"[{s}]" for s in black))
    if white:
        lines.append("AW" + "".join(f"[{s}]" for s in white))
    lines.append(")")

    with open(filename, "w") as f:
        f.write("\n".join(lines))
    return len(black), len(white)

# === Display Helpers ===
def print_board(board):
    symbols = {0: ".", 1: "X", 2: "O"}
    col_labels = "A B C D E F G H J K L M N O P Q R S T"
    print(f"   {col_labels}")
    for r in range(BOARD_SIZE):
        row_num = BOARD_SIZE - r
        row_str = " ".join(symbols[board[r, c]] for c in range(BOARD_SIZE))
        print(f"{row_num:2d} {row_str} {row_num:2d}")
    print(f"   {col_labels}")

def draw_overlay(img, intersections, board):
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

# === Main Pipeline ===
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "board.jpg"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = "scans"
    os.makedirs(out_dir, exist_ok=True)

    print("=== Go Board Vision Pipeline ===\n")
    t_start = time.time()

    print("[1/5] Loading image...")
    img = load_image(path)

    print("[2/5] Select the 4 board corners (TL, TR, BR, BL)...")
    src_corners = select_corners(img)
    warped = warp_board(img, src_corners)
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    print("  Board warped.")

    print("[3/5] Detecting grid...")
    intersections = find_grid(gray)
    print(f"  Mapped {BOARD_SIZE}x{BOARD_SIZE} grid.")

    print("[4/5] Detecting stones...")
    board = detect_stones(gray, intersections)
    b = np.count_nonzero(board == 1)
    w = np.count_nonzero(board == 2)
    print(f"  Found {b} black, {w} white stones.")

    print("[5/5] Exporting SGF...")
    sgf_path = os.path.join(out_dir, f"game_{timestamp}.sgf")
    export_sgf(board, sgf_path)
    print(f"  Saved {sgf_path}")

    elapsed = time.time() - t_start
    print(f"\nPipeline completed in {elapsed:.2f}s\n")
    print_board(board)

    # Save outputs
    warped_path = os.path.join(out_dir, f"warped_{timestamp}.jpg")
    overlay_path = os.path.join(out_dir, f"overlay_{timestamp}.jpg")
    cv2.imwrite(warped_path, warped)
    cv2.imwrite(overlay_path, draw_overlay(warped, intersections, board))
    print(f"\nSaved: {warped_path}, {overlay_path}, {sgf_path}")

    cv2.imshow("Result (press any key)", draw_overlay(warped, intersections, board))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()