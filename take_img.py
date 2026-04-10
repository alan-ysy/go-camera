from picamera2 import Picamera2

IMG_DIR = 'board-img/'

cam = Picamera2()
cam.configure(cam.create_still_configuration())
cam.start()
cam.capture_file(IMG_DIR + 'board.jpg')
cam.stop()
print('Camera OK - Image saved')
