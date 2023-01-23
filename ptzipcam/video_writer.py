"""Classes for writing outputs to video files

"""

import cv2


class DilationVideoWriter():
    """Manages writing of video with built in time dilation

    """


    def __init__(self,
                 output_file,
                 codec,
                 frame_rate,
                 frame_shape,
                 frame_window):

        self.frame_window = frame_window

        self.interval = 10
        self.latch_count = 0

        self.out = cv2.VideoWriter(output_file,
                                   codec,
                                   frame_rate,
                                   frame_shape)
        self.count = 0

    def update(self, frame, target_detected):
        """Updates the video writer

        Method to run each time through control loop that writes a
        frame to video a file based on the desired time dilation
        mechanics.

        """
        if target_detected:
            self.interval = 1
            # any time detected restart latch_count
            self.latch_count = 0

        self.latch_count += 1
        if self.latch_count > self.frame_window:
            self.interval = 10
            self.latch_count = 0

        self.count += 1
        if self.count >= self.interval:
            self.out.write(frame)
            self.count = 0

    def release(self):
        """Release VideoWriter object

        """
        self.out.release()
