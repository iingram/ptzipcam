import os
import time

import cv2


class ImageStreamRecorder():

    def __init__(self, path):
        self.path = path
        self.record_file = time.strftime("%Y-%m-%dT%H:%M:%S") + '.csv'
        self.record_file = os.path.join(self.path, self.record_file)
        with open(self.record_file, 'w') as f:
            f.write('IMAGE_FILE, PAN_ANGLE, TILT_ANGLE\n')

    def record_image(self, image, pan_angle, tilt_angle):
        front_bit = time.strftime("%Y-%m-%dT%H:%M:%S")
        image_filename = front_bit + '.jpg'
        full_path = os.path.join(self.path, 'images')
        image_filename_w_path = os.path.join(full_path, image_filename)
        cv2.imwrite(image_filename_w_path, image)

        record_line = '{},{:.2f},{:.2f}\n'.format(image_filename,
                                                  pan_angle,
                                                  tilt_angle)
        with open(self.record_file, 'a') as f:
            f.write(record_line)
