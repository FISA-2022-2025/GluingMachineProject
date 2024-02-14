from PySide6.QtCore import QThread

class CameraBufferCleanerThread(QThread):
    '''Thread to continously pull frames from the camera.'''
    def __init__(self, camera):
            self.camera = camera
            self.last_frame = None
            super(CameraBufferCleanerThread, self).__init__()
            self.start()
    def run(self):
        while True:
            ret, self.last_frame = self.camera.read()
