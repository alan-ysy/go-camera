from picamera2 import Picamera2

IMG_DIR = 'test-img/'

cam = Picamera2()
cam.configure(cam.create_still_configuration())
cam.start()
cam.capture_file(IMG_DIR + 'test.jpg')
cam.stop()
print('Camera OK — test.jpg saved')
