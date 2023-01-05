import logging
import threading
import cv2

# latest_frame = None
# latest_frame_return = None
# lo = threading.Lock()

log = logging.getLogger(__name__)

def camera_thread_function(cap, frame):
    # global latest_frame, lo, latest_frame_return
    while True:
        # with lo:
        # latest_frame_return, latest_frame = cap.read()
        ok, frame[0] = cap.read()


class Camera():

    # def __init__(self, address='udp://127.0.0.1:5000'):
    def __init__(self,
                 ip,
                 user,
                 passwd,
                 stream=3,
                 rtsp_port=554,
                 cam_brand='hikvision'):

        if cam_brand == 'axis':
            stream_string = (':'
                             + str(rtsp_port)
                             + '/axis-media/media.amp')
        elif cam_brand == 'hikvision':
            stream_string = (':'
                             + str(rtsp_port)
                             + '/Streaming/Channels/10'
                             + str(stream))
        else:
            print('[ERROR] Camera type not recognized.')
            
        address = ('rtsp://'
                   + user
                   + ':'
                   + passwd
                   + '@'
                   + ip
                   + stream_string)
        self.frame = [None]
        # self.cap = cv2.VideoCapture(address, cv2.CAP_FFMPEG)
        self.cap = cv2.VideoCapture(address)
        ok, self.frame[0] = self.cap.read()

        self.cam_thread = threading.Thread(target=camera_thread_function,
                                           args=(self.cap, self.frame))
        self.cam_thread.daemon = True
        self.cam_thread.start()

    def get_frame(self):
        # if (latest_frame_return is not None) and (latest_frame is not None):
        #     self.frame = latest_frame.copy()

        return self.frame[0]

    def get_resolution(self):
        return self.frame[0].shape[1], self.frame[0].shape[0]

    # def release(self):
    #     self.cap.release()

    def __del__(self):
        log.info('Camera object deletion')
        self.cap.release()
