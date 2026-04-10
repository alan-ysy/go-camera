"""
Board Warp Tool
- Run with an image path as argument
- Click the 4 corners of the board (top-left, top-right, bottom-right, bottom-left)
- Press ENTER to warp, Q to quit
- Saves the warped result as warped_board.jpg
"""

import cv2
import numpy as np
import sys

OUTPUT_SIZE = 800  # output square size in pixels

corners = []

def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(corners) < 4:
        corners.append((x, y))
        print(f"Corner {len(corners)}: ({x}, {y})")

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "board.jpg"
    img = cv2.imread(path)
    if img is None:
        print(f"Could not load {path}")
        return

    # Resize for display if too large
    h, w = img.shape[:2]
    scale = min(1.0, 1200 / max(h, w))
    display = cv2.resize(img, (int(w * scale), int(h * scale)))

    cv2.namedWindow("Select 4 corners: TL, TR, BR, BL")
    cv2.setMouseCallback("Select 4 corners: TL, TR, BR, BL", on_click)

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

        cv2.imshow("Select 4 corners: TL, TR, BR, BL", vis)
        key = cv2.waitKey(30) & 0xFF

        if key == 13 and len(corners) == 4:  # ENTER
            break
        elif key == ord('r'):  # Reset
            corners.clear()
            print("Corners reset")
        elif key == ord('q'):
            cv2.destroyAllWindows()
            return

    # Scale corners back to original image coordinates
    src = np.array([(int(x / scale), int(y / scale)) for x, y in corners], dtype=np.float32)
    dst = np.array([
        [0, 0],
        [OUTPUT_SIZE, 0],
        [OUTPUT_SIZE, OUTPUT_SIZE],
        [0, OUTPUT_SIZE]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (OUTPUT_SIZE, OUTPUT_SIZE))

    cv2.imwrite("warped_board.jpg", warped)
    print("Saved warped_board.jpg")

    cv2.imshow("Warped Board", warped)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()