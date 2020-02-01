import threading
import cv2

# latest_frame = None
# latest_frame_return = None
# lo = threading.Lock()


def camera_thread_function(cap, frame):
    # global latest_frame, lo, latest_frame_return
    while True:
        # with lo:
        # latest_frame_return, latest_frame = cap.read()
        ok, frame[0] = cap.read()


class Camera():

    # def __init__(self, address='udp://127.0.0.1:5000'):
    def __init__(self, ip='192.168.1.64', user='admin', passwd='NyalaChow22'):
        address='rtsp://' + user + ':' + passwd + '@' + ip + ':554/Streaming/Channels/103'
        self.frame = [None]
        # self.cap = cv2.VideoCapture(address, cv2.CAP_FFMPEG)
        self.cap = cv2.VideoCapture(address)
        ok, self.frame[0] = self.cap.read()

        self.cam_thread = threading.Thread(target=camera_thread_function,
                                           args=(self.cap, self.frame))
        self.cam_thread.start()

    def get_frame(self):
        # if (latest_frame_return is not None) and (latest_frame is not None):
        #     self.frame = latest_frame.copy()

        return self.frame[0]

    def get_resolution(self):
        return self.frame[0].shape[1], self.frame[0].shape[0]

    def release(self):
        self.cap.release()
