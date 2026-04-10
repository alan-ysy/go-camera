from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from libcamera import Transform
import sys

app = QApplication(sys.argv)
cam = Picamera2()
flipped = False

def configure_camera():
    cam.stop()
    transform = Transform(hflip=flipped, vflip=flipped)
    cam.configure(cam.create_preview_configuration(main={"size": (1920, 1080)}, transform=transform))
    cam.start()

cam.configure(cam.create_preview_configuration(main={"size": (1920, 1080)}))
window = QGlPicamera2(cam, width=800, height=600)
window.setWindowTitle("Go Board Preview - R to rotate, Q to quit")
cam.start()

original_key_handler = window.keyPressEvent

def key_handler(event):
    global flipped
    if event.key() == Qt.Key_R:
        flipped = not flipped
        configure_camera()
    elif event.key() == Qt.Key_Q:
        cam.stop()
        app.quit()
    else:
        original_key_handler(event)

window.keyPressEvent = key_handler
window.show()
sys.exit(app.exec_())