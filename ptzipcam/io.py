import os
import time
import math

from datetime import datetime
import cv2


class ImageStreamRecorder():

    def __init__(self, path):
        self.path = path
        timestamp_string = time.strftime("%Y-%m-%dT%H:%M:%S")
        image_folder_name = timestamp_string + '_images'
        self.image_path = os.path.join(self.path, image_folder_name)
        if not os.path.exists(self.image_path):
            os.mkdir(self.image_path)
        else:
            print('[WARNING] Images path already exists so there could end up being \
            images from two runs in one folder or worse images could \
            be over written (not too likely as they have millisecond \
            timestamps but not impossible.).  This also means that is \
            likely a system clock is off for the folder name (also \
            timestamped) to be duplicate') 
        self.record_file = timestamp_string + '.csv'
        self.record_file = os.path.join(self.path, self.record_file)
        with open(self.record_file, 'w') as f:
            f.write('IMAGE_FILE, PAN_ANGLE, TILT_ANGLE\n')

    def record_image(self, image, pan_angle, tilt_angle):
        front_bit = time.strftime("%Y-%m-%dT%H:%M:%S")
        # maybe you should avoid a call to time and datetime and just
        # get everything from datetime. later.
        dt = datetime.now()
        front_bit = front_bit + '_{:03d}'.format(math.floor(dt.microsecond/1000))
        image_filename = front_bit + '.jpg'
        
        # full_path = os.path.join(self.path, 'images')
        # if not os.path.exists(full_path):
        #     os.mkdir(full_path)

        image_filename_w_path = os.path.join(self.image_path,
                                             image_filename)
        cv2.imwrite(image_filename_w_path, image)

        record_line = '{},{:.2f},{:.2f}\n'.format(image_filename,
                                                  pan_angle,
                                                  tilt_angle)
        with open(self.record_file, 'a') as f:
            f.write(record_line)