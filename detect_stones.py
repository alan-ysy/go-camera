"""
Stone Detector
- Loads a warped board image and grid.npy
- Classifies each intersection as empty (0), black (1), or white (2)
- Outputs a visual overlay and prints the board state
"""

import cv2
import numpy as np
import sys

BOARD_SIZE = 19
ROI_RADIUS = 12  # pixels around each intersection to sample

def classify_intersections(gray, intersections):
    """Classify each intersection based on brightness and uniformity."""
    h, w = gray.shape
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)

    # First pass: collect stats at every intersection
    means = np.zeros((BOARD_SIZE, BOARD_SIZE))
    stds = np.zeros((BOARD_SIZE, BOARD_SIZE))
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x, y = int(intersections[r, c, 0]), int(intersections[r, c, 1])
            y0 = max(0, y - ROI_RADIUS)
            y1 = min(h, y + ROI_RADIUS)
            x0 = max(0, x - ROI_RADIUS)
            x1 = min(w, x + ROI_RADIUS)
            roi = gray[y0:y1, x0:x1]
            means[r, c] = np.mean(roi)
            stds[r, c] = np.std(roi)

    # Board color baseline from median (most intersections are empty)
    median_val = np.median(means)
    # Empty intersections have higher std (grid lines), stones are more uniform
    median_std = np.median(stds)

    black_thresh = median_val - 40
    white_thresh = median_val + 20

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            is_uniform = stds[r, c] < median_std  # stone-like uniformity
            if means[r, c] < black_thresh and is_uniform:
                board[r, c] = 1  # black
            elif means[r, c] > white_thresh and is_uniform:
                board[r, c] = 2  # white
            else:
                board[r, c] = 0  # empty

    return board

def draw_overlay(img, intersections, board):
    """Draw detected stones on the image."""
    overlay = img.copy()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x, y = int(intersections[r, c, 0]), int(intersections[r, c, 1])
            if board[r, c] == 1:  # black
                cv2.circle(overlay, (x, y), ROI_RADIUS, (255, 0, 0), 2)
                cv2.circle(overlay, (x, y), 2, (255, 0, 0), -1)
            elif board[r, c] == 2:  # white
                cv2.circle(overlay, (x, y), ROI_RADIUS, (0, 255, 0), 2)
                cv2.circle(overlay, (x, y), 2, (0, 255, 0), -1)
    return overlay

def print_board(board):
    """Print a text representation of the board."""
    symbols = {0: ".", 1: "X", 2: "O"}
    col_labels = "A B C D E F G H J K L M N O P Q R S T"
    print(f"   {col_labels}")
    for r in range(BOARD_SIZE):
        row_num = BOARD_SIZE - r
        row_str = " ".join(symbols[board[r, c]] for c in range(BOARD_SIZE))
        print(f"{row_num:2d} {row_str} {row_num:2d}")
    print(f"   {col_labels}")

def main():
    img_path = sys.argv[1] if len(sys.argv) > 1 else "warped_board.jpg"
    grid_path = sys.argv[2] if len(sys.argv) > 2 else "grid.npy"

    img = cv2.imread(img_path)
    if img is None:
        print(f"Could not load {img_path}")
        return

    intersections = np.load(grid_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    board = classify_intersections(gray, intersections)
    print_board(board)

    overlay = draw_overlay(img, intersections, board)
    cv2.imwrite("detected_stones.jpg", overlay)
    np.save("board_state.npy", board)
    print("\nSaved detected_stones.jpg and board_state.npy")

    cv2.imshow("Detected Stones (press any key)", overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()