import os
import time
import math

from datetime import datetime
import cv2


class ImageStreamRecorder():

    def __init__(self, path):
        self.path = path
        self.timestamp_format = "%Y-%m-%dT%H-%M-%S"
        timestamp_string = time.strftime(self.timestamp_format)
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
            f.write('IMAGE_FILE,PAN_ANGLE,TILT_ANGLE,ZOOM_POWER,CLASS,SCORE,X,Y,W,H\n')

    def record_image(self,
                     image,
                     ptz_state,
                     detected_class,
                     target_lbox):

        pan_angle, tilt_angle, zoom = ptz_state

        front_bit = time.strftime(self.timestamp_format)
        # maybe you should avoid a call to time and datetime and just
        # get everything from datetime. later.
        dt = datetime.now()
        front_bit = (front_bit
                     + '_{:03d}'.format(math.floor(dt.microsecond/1000)))
        image_filename = front_bit + '.jpg'

        # full_path = os.path.join(self.path, 'images')
        # if not os.path.exists(full_path):
        #     os.mkdir(full_path)

        image_filename_w_path = os.path.join(self.image_path,
                                             image_filename)
        cv2.imwrite(image_filename_w_path, image)

        if target_lbox:
            score = 100 * target_lbox['confidence']
            x, y, w, h = target_lbox['box']
        else:
            score = 0
            x = 0
            y = 0
            w = 0
            h = 0

        strg = '{},{:.2f},{:.2f},{:.2f},{},{:.1f},{},{},{},{}\n'
        record_line = strg.format(image_filename,
                                  pan_angle,
                                  tilt_angle,
                                  zoom,
                                  detected_class,
                                  score,
                                  x,
                                  y,
                                  w,
                                  h)

        with open(self.record_file, 'a') as f:
            f.write(record_line)
