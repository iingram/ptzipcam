"""Elements for image capture aspects of network cameras

"""
import logging
import threading
import cv2

# latest_frame = None
# latest_frame_return = None
# lo = threading.Lock()

log = logging.getLogger(__name__)


def camera_thread_function(cap, frame):
    """Thread function to constantly capture frames

    """
    # global latest_frame, lo, latest_frame_return
    while True:
        # with lo:
        # latest_frame_return, latest_frame = cap.read()
        _, frame[0] = cap.read()


class Camera():
    """Handles image capture from network camera

    """

    # def __init__(self, address='udp://127.0.0.1:5000'):
    def __init__(self,
                 ip_address,
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
                   + ip_address
                   + stream_string)
        self.frame = [None]
        # self.cap = cv2.VideoCapture(address, cv2.CAP_FFMPEG)
        self.cap = cv2.VideoCapture(address)
        _, self.frame[0] = self.cap.read()

        self.cam_thread = threading.Thread(target=camera_thread_function,
                                           args=(self.cap, self.frame))
        self.cam_thread.daemon = True
        self.cam_thread.start()

    def get_frame(self):
        """Grab frame from RTSP stream

        """
        # if (latest_frame_return is not None) and (latest_frame is not None):
        #     self.frame = latest_frame.copy()

        return self.frame[0]

    def get_resolution(self):
        """Get resolution of current camera stream

        """
        return self.frame[0].shape[1], self.frame[0].shape[0]

    def release(self):
        """Release the cv2.VideoCapture object

        """
        log.info("Release camera object's capture object.")
        self.cap.release()

    def __del__(self):
        """Destructor

        Included for logging/tracking of object deletion and to make
        sure cv2.VideoCapture object is released as there is concern
        that automatic garbage collection might not deal with this
        completely.

        """

        log.info('Camera object deletion')
        self.cap.release()
