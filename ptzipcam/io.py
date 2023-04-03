"""Tools for recording output from camera applications

At this stage, this amounts to a single class for recording stills.


"""
import logging
import os

from datetime import datetime
import cv2

log = logging.getLogger(__name__)


class ImageStreamRecorder():  # pylint: disable=too-few-public-methods
    """Handles recording images with their associate metadata

    The metadata are the PTZ state when the image was captured and
    objection detection (bounding box data, detected class, score)
    tied to that images capture.

    """

    def __init__(self, path):
        log.debug('Initialize recorder.')
        self.path = path
        self.timestamp_format = "%Y-%m-%dT%H-%M-%S_%f"
        timestamp_string = datetime.now().strftime(self.timestamp_format[:-3])
        image_folder_name = timestamp_string + '_images'
        self.image_path = os.path.join(self.path, image_folder_name)
        if not os.path.exists(self.image_path):
            os.mkdir(self.image_path)
        else:
            warning = ('[WARNING] Images path already exists so there could '
                       'end up being images from two runs in one folder or '
                       'worse images could be over-written (not too likely as '
                       'they have millisecond timestamps but not impossible.).'
                       ' This also means that it is likely a system clock is '
                       'off for the folder name (also timestamped) to be '
                       'duplicate')
            log.warning(warning)
        self.record_filename = timestamp_string + '.csv'
        self.record_filename = os.path.join(self.path, self.record_filename)
        with open(self.record_filename, 'w', encoding='utf-8') as record_file:
            header_line = ('IMAGE_FILE,PAN_ANGLE,TILT_ANGLE,'
                           'ZOOM_POWER,CLASS,SCORE,X,Y,W,H\n')
            record_file.write(header_line)

    def record_image(self,  # pylint: disable=too-many-locals
                     image,
                     ptz_state,
                     detected_class,
                     target_lbox):
        """Record a single image to a file and append the associated PTZ state
        and object detection data to the recording CSV file.

        Parameters
        ----------

        image :
            The image to record

        ptz_state : 3-tuple
            Contains the pan, tilt, zoom of the camera at the time the
            image was captured.

        detected_class :
            The name of the detected class

        target_lbox : dict
            The parameters of the labeled bounding box of the detected target.

        """

        pan_angle, tilt_angle, zoom = ptz_state

        front_bit = datetime.now().strftime(self.timestamp_format)[:-3]
        image_filename = front_bit + '.jpg'

        # full_path = os.path.join(self.path, 'images')
        # if not os.path.exists(full_path):
        #     os.mkdir(full_path)

        image_filename_w_path = os.path.join(self.image_path,
                                             image_filename)
        cv2.imwrite(image_filename_w_path, image)

        if target_lbox:
            score = 100 * target_lbox['confidence']
            box = target_lbox['box']
            box_x_coord, box_y_coord, box_width, box_height = box
        else:
            score = 0
            box_x_coord = 0
            box_y_coord = 0
            box_width = 0
            box_height = 0

        strg = '{},{:.2f},{:.2f},{:.2f},{},{:.1f},{},{},{},{}\n'
        record_line = strg.format(image_filename,
                                  pan_angle,
                                  tilt_angle,
                                  zoom,
                                  detected_class,
                                  score,
                                  box_x_coord,
                                  box_y_coord,
                                  box_width,
                                  box_height)

        with open(self.record_filename, 'a', encoding='utf-8') as record_file:
            record_file.write(record_line)
