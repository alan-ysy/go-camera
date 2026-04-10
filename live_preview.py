"""
Raspberry Pi Camera Capture
- Shows a live preview using the Picamera2 library
- Press SPACE to save the current frame as a timestamped JPEG at full resolution
- Press R to toggle 180° rotation (for upside-down mounted cameras)
- Press Q to quit
"""

from picamera2 import Picamera2
import cv2
import time

PREVIEW_HEIGHT = 720

def main():
    picam2 = Picamera2()
    # Use the full sensor resolution for the main stream
    full_res = picam2.sensor_resolution
    config = picam2.create_preview_configuration(main={"size": full_res, "format": "RGB888"})
    picam2.configure(config)
    picam2.start()
    time.sleep(1)

    flipped = False
    print(f"Capturing at {full_res[0]}x{full_res[1]}")
    print("SPACE = capture, R = flip 180°, Q = quit")

    while True:
        frame = picam2.capture_array()

        if flipped:
            frame = cv2.rotate(frame, cv2.ROTATE_180)

        # Scale down for the preview window
        h, w = frame.shape[:2]
        scale = PREVIEW_HEIGHT / h
        preview = cv2.resize(frame, (int(w * scale), PREVIEW_HEIGHT))

        cv2.imshow("Pi Camera Preview", preview)
        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):
            filename = time.strftime("capture_%Y%m%d_%H%M%S.jpg")
            cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            print(f"Saved {filename} ({w}x{h})")
        elif key == ord('r'):
            flipped = not flipped
            print(f"Rotation {'on' if flipped else 'off'}")
        elif key == ord('q'):
            break

    picam2.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()