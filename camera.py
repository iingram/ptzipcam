import threading
import cv2

latest_frame = None
latest_frame_return = None
lo = threading.Lock()

def camera_thread_function(cap):
    global latest_frame, lo, latest_frame_return
    while True:
        with lo:
            latest_frame_return, latest_frame = cap.read()

            
class Camera():

    def __init__(self):
        self.frame = None
        self.cap = cv2.VideoCapture('udp://127.0.0.1:5000', cv2.CAP_FFMPEG)
        ok, self.frame = self.cap.read()

        self.cam_thread = threading.Thread(target=camera_thread_function,
                                      args=(self.cap,))
        self.cam_thread.start()
        
    def get_frame(self):
        if (latest_frame_return is not None) and (latest_frame is not None):
            self.frame = latest_frame.copy()

        return self.frame

    def release(self):
        self.cap.release()

        
