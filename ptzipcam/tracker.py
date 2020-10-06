import os

from ptzipcam.camera import Camera
from ptzipcam import ui

from dnntools import neuralnetwork as nn
# from dnntools import neuralnetwork_coral as nn

from dnntools import draw


class Tracker():
    
    def __init__(self, configs):
        
        IP = configs['IP']
        USER = configs['USER']
        PWORD = configs['PASS']
        STREAM = configs['STREAM']    
        self.cam = Camera(ip=IP, user=USER, passwd=PWORD, stream=STREAM)

        frame = self.cam.get_frame()
        self.frame_width = frame.shape[1]
        self.frame_height = frame.shape[0]

        # self.total_pixels = self.frame_width * self.frame_height
        
        self.ORIENTATION = configs['ORIENTATION']

        # CV constants
        self.TRACKED_CLASS = configs['TRACKED_CLASS']
        self.CONF_THRESHOLD = configs['CONF_THRESHOLD']
        self.NMS_THRESHOLD = configs['NMS_THRESHOLD']
        INPUT_WIDTH = configs['INPUT_WIDTH']
        INPUT_HEIGHT = configs['INPUT_HEIGHT']

        
        MODEL_PATH = configs['MODEL_PATH']
        MODEL_CONFIG = os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
        MODEL_WEIGHTS = os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
        CLASSES_FILE = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
        self.CLASSES = nn.read_classes_from_file(CLASSES_FILE)

        self.network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                                MODEL_WEIGHTS,
                                                INPUT_WIDTH,
                                                INPUT_HEIGHT)

        self.detected_class = 'Nothing'
        
        self.x_err = 0
        self.y_err = 0
        self.target_present = False
        self.status = 'Just got going.'

        self.frames_since_last_acq = 0
        
    def get_errors(self):
        return self.x_err, self.y_err
        
    def update(self):
        raw_frame = self.cam.get_frame()
        if raw_frame is None:
            # probably should do something with logging here
            self.status = 'Frame is None.'
            return

        # maybe the orient_frame method should not be part of ui
        # module as that is the only reason I am importing the ui
        # module into this non-UI-ish module.
        raw_frame = ui.orient_frame(raw_frame, self.ORIENTATION)
        frame = raw_frame.copy()

        outs, self.inference_time = self.network.infer(frame)

        lboxes = self.network.filter_boxes(outs,
                                           frame,
                                           self.CONF_THRESHOLD,
                                           self.NMS_THRESHOLD)


        # extract the lbox with the highest confidence (that is a target type)
        highest_confidence_tracked_class = 0
        target_lbox = None
        for lbox in lboxes:
            if self.CLASSES[lbox['class_id']] in self.TRACKED_CLASS:
                if lbox['confidence'] > highest_confidence_tracked_class:
                    highest_confidence_tracked_class = lbox['confidence']
                    target_lbox = lbox

        # if there is an appropriate lbox attempt to adjust ptz cam
        self.detected_class = 'nothing detected'
        # score = 0.0
        if target_lbox:
            self.target_present = True
            self.detected_class = self.CLASSES[target_lbox['class_id']]

            self.frames_since_last_acq = 0
            xc, yc = draw.box_to_coords(target_lbox['box'],
                                        return_kind='center')
            coords = draw.box_to_coords(target_lbox['box'])
            x, y, box_width, box_height = coords
            self.x_err = self.frame_width/2 - xc
            self.y_err = self.frame_height/2 - yc

            # target_bb_pixels = box_width * box_height
            # if (target_bb_pixels / total_pixels) < .3:
            #     zoom_command += .1
            #     if zoom_command >= 1.0:
            #         zoom_command = 1.0
            #     # zoom_command = 1.0
            # else:
            #     zoom_command = 0.0

            # filling_much_of_width = box_width >= .7 * frame_width
            # filling_much_of_height = box_height >= .7 * frame_height
            # if filling_much_of_width or filling_much_of_height:
            #     zoom_command = 0.0
        else:
            self.target_present = False
            #zoom_command = 0
            self.frames_since_last_acq += 1
            if self.frames_since_last_acq > 10:
                x_err = 0
                y_err = 0

            # if frames_since_last_acq > 30:
            #     zoom_command -= .05
            #     if zoom_command <= -1.0:
            #         zoom_command = -1.0
            #     # zoom_command = -1.0

