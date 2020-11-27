#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os
import time
import argparse

import yaml

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.ptz_camera import MotorController
from ptzipcam.camera import Camera
from ptzipcam import ui
from ptzipcam.io import ImageStreamRecorder
# from ptzipcam.video_writer import DilationVideoWriter

# from dnntools import neuralnetwork as nn
from dnntools import neuralnetwork_coral as nn

from dnntools import draw

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

# DILATION = True
FRAME_RATE = 15
FRAME_WINDOW = 30

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']
STREAM = configs['STREAM']

# ptz camera setup constants
INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']
PID_GAINS = configs['PID_GAINS']

# CV constants
TRACKED_CLASS = configs['TRACKED_CLASS']
CONF_THRESHOLD = configs['CONF_THRESHOLD']
NMS_THRESHOLD = configs['NMS_THRESHOLD']
INPUT_WIDTH = configs['INPUT_WIDTH']
INPUT_HEIGHT = configs['INPUT_HEIGHT']

MODEL_PATH = configs['MODEL_PATH']
MODEL_CONFIG = os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
MODEL_WEIGHTS = os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
CLASSES_FILE = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
CLASSES = nn.read_classes_from_file(CLASSES_FILE)

# GUI constants
HEADLESS = configs['HEADLESS']


class Perception():

    def __init__(self):
        self.network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                                MODEL_WEIGHTS,
                                                INPUT_WIDTH,
                                                INPUT_HEIGHT)

    def update(self, frame):
        outs, inference_time = self.network.infer(frame)
        msg = ("[INFO] Inference time: "
               + "{:.1f} milliseconds".format(inference_time))
        print(msg)
        lboxes = self.network.filter_boxes(outs,
                                           frame,
                                           CONF_THRESHOLD,
                                           NMS_THRESHOLD)

        # extract the lbox with the highest confidence (that is a target type)
        highest_confidence_tracked_class = 0
        target_lbox = None
        for lbox in lboxes:
            if CLASSES[lbox['class_id']] in TRACKED_CLASS:
                if lbox['confidence'] > highest_confidence_tracked_class:
                    highest_confidence_tracked_class = lbox['confidence']
                    target_lbox = lbox

        return target_lbox


if __name__ == '__main__':
    # construct core objects
    ptz = PtzCam(IP, PORT, USER, PASS)
    # cam = Camera()
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)

    motor_controller = MotorController(PID_GAINS, ORIENTATION)

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)

    perception = Perception()

    window_name = 'Detect, Track, and Zoom'

    if not HEADLESS:
        uih = ui.UI_Handler(frame, window_name)

    print("[INFO] Using: " + nn.__name__)

    frame = cam.get_frame()
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]

    total_pixels = frame_width * frame_height

    if RECORD:
        recorder = ImageStreamRecorder('/home/ian/images_dtz')

        # codec = cv2.VideoWriter_fourcc(*'MJPG')
        # filename = 'video_dtz'
        # if 'neuralnetwork_coral' in nn.__name__:
        #     filename = filename + '_coral'
        # else:
        #     filename = filename + '_dnn'

        # if not DILATION:
        #     filename = filename + '_lineartime' + '.avi'
        #     vid_writer = cv2.VideoWriter(filename,
        #                                  codec,
        #                                  FRAME_RATE,
        #                                  (frame_width, frame_height))
        # else:
        #     filename = filename + '_dilation' + '.avi'
        #     dilation_vid_writer = DilationVideoWriter(filename,
        #                                               codec,
        #                                               FRAME_RATE,
        #                                               (frame_width, frame_height),
        #                                               FRAME_WINDOW)

    # initialize position of camera
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)
    pan, tilt, zoom = ptz.get_position()
    # ptz.absmove(INIT_POS[0], INIT_POS[1])
    pan_init = INIT_POS[0]/180.0
    tilt_init = INIT_POS[1]/45.0
    zoom_init = INIT_POS[2]/25.0

    ptz.absmove_w_zoom_waitfordone(pan_init,
                                   tilt_init,
                                   zoom_init,
                                   close_enough=.01)

    x_err = 0
    y_err = 0

    frames_since_last_acq = 0

    while True:
        pan, tilt, zoom = ptz.get_position()
        # print("Zoom is at: " + str(zoom))

        raw_frame = cam.get_frame()
        if raw_frame is None:
            print('Frame is None.')
            continue

        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        target_lbox = perception.update(frame)

        # if there is an appropriate lbox attempt to adjust ptz cam
        detected_class = 'nothing detected'
        score = 0.0
        if target_lbox:
            detected_class = CLASSES[target_lbox['class_id']]
            score = 100 * target_lbox['confidence']
            print("[INFO] Detected: "
                  + "{} with confidence {:.1f}".format(detected_class,
                                                       score))

            frames_since_last_acq = 0
            draw.labeled_box(frame, CLASSES, target_lbox)
            xc, yc = draw.box_to_coords(target_lbox['box'],
                                        return_kind='center')
            ret = draw.box_to_coords(target_lbox['box'])
            x, y, box_width, box_height = ret
            x_err = frame_width/2 - xc
            y_err = frame_height/2 - yc

            target_bb_pixels = box_width * box_height

            # if x_err < 50 and y_err < 50:
            # if x_err != 0 and x_err < 50 and y_err < 50:
            if (target_bb_pixels / total_pixels) < .3:
                zoom_command += .1
                if zoom_command >= 1.0:
                    zoom_command = 1.0
                # zoom_command = 1.0
            else:
                zoom_command = 0.0

            filling_much_of_width = box_width >= .7 * frame_width
            filling_much_of_height = box_height >= .7 * frame_height
            if filling_much_of_width or filling_much_of_height:
                zoom_command = 0.0
        else:
            zoom_command = 0
            # print(str(time.time()) + ': no target')
            frames_since_last_acq += 1
            if frames_since_last_acq > 10:
                x_err = 0
                y_err = 0

            if frames_since_last_acq > 30:
                # x_err = -300
                x_err = 0

            # # commenting this bit out because it doesn't always work
            # # and may be source of wandering bug
            # if frames_since_last_acq > 30:
            #     ptz.absmove(INIT_POS[0], INIT_POS[1])
            if frames_since_last_acq > 30:
                zoom_command -= .05
                if zoom_command <= -1.0:
                    zoom_command = -1.0
                # zoom_command = -1.0

        # update ui and handle user input

        if not HEADLESS:
            key = uih.update(frame, hud=False)
            if key == ord('q'):
                break

        if RECORD:
            recorder.record_image(frame,
                                  pan,
                                  tilt,
                                  detected_class,
                                  score)

            # if not DILATION:
            #     vid_writer.write(frame.astype(np.uint8))
            # else:
            #     dilation_vid_writer.update(frame, target_lbox is not None)

        # run position controller on ptz system
        x_velocity, y_velocity = motor_controller.run(x_err, y_err)
        if x_velocity == 0 and y_velocity == 0 and zoom < 0.001:
            # print('stop action')
            ptz.stop()

        ptz.move_w_zoom(x_velocity, y_velocity, zoom_command)

    # if RECORD:
    #     if not DILATION:
    #         vid_writer.release()
    #     else:
    #         dilation_vid_writer.release()
    del cam
    ptz.stop()
    if not HEADLESS:
        uih.clean_up()
