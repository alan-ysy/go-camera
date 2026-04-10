from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys
import os

SAVE_DIR = "board-img"
os.makedirs(SAVE_DIR, exist_ok=True)

counter = 1

app = QApplication(sys.argv)
cam = Picamera2()
cam.configure(cam.create_preview_configuration())
cam.start()

window = QGlPicamera2(cam, width=800, height=600)
window.setWindowTitle("Go Board Preview - Press SPACE to capture, Q to quit")

def key_handler(event):
    global counter
    if event.key() == Qt.Key_Space:
        path = os.path.join(SAVE_DIR, f"board-{counter}.jpg")
        cam.capture_file(path)
        print(f"Saved: {path}")
        counter += 1
    elif event.key() == Qt.Key_Q:
        cam.stop()
        app.quit()

window.keyPressEvent = key_handler
window.show()
sys.exit(app.exec_())
