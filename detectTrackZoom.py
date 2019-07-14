#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os
import yaml
# import time

from ptz_camera import PtzCam
from camera import Camera
import ui

from zooSpotter import neuralnetwork as nn
from zooSpotter import draw

with open('configs.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

TRACKED_CLASS = 'person'
    
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']

CONF_THRESHOLD = configs['CONF_THRESHOLD']
NMS_THRESHOLD = configs['NMS_THRESHOLD']
INPUT_WIDTH = configs['INPUT_WIDTH']
INPUT_HEIGHT = configs['INPUT_HEIGHT']

MODEL_PATH = configs['MODEL_PATH']

model_config = os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
model_weights = os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
classes_file = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
classes = nn.read_classes_from_file(classes_file)

def checkZeroness(number):
    e = .001

    if number < e and number > -e:
        return 0
    else:
        return number

if __name__ == '__main__':
    ptzCam = PtzCam(IP, PORT, USER, PASS)
    cam = Camera()

    frame = cam.get_frame()
    ui = ui.UI_Handler(frame)

    network = nn.NeuralNetworkHandler(model_config,
                                      model_weights,
                                      INPUT_WIDTH,
                                      INPUT_HEIGHT)

    x_dir = 0
    y_dir = 0
    zoom_command = 0
    ptzCam.zoom_out_full()
    # ptzCam.absmove(-1, 0)
    # time.sleep(10)
    
    x_err = 0
    y_err = 0

    frame = cam.get_frame()
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    
    while True:
        frame = cam.get_frame()
        outs, inferenceTime = network.infer(frame)
        lboxes = nn.NeuralNetworkHandler.filterBoxes(outs,
                                                     frame,
                                                     CONF_THRESHOLD,
                                                     NMS_THRESHOLD)

        highest_confidence_tracked_class = 0
        target_lbox= None
        for lbox in lboxes:
            if classes[lbox['classId']] == TRACKED_CLASS:
                if lbox['confidence'] > highest_confidence_tracked_class:
                    highest_confidence_tracked_class = lbox['confidence']
                    target_lbox = lbox

        if target_lbox:
            draw.labeledBox(frame, classes, target_lbox)
            xc, yc = draw.box_to_coords(target_lbox['box'], return_kind='center')
            x, y, box_width, box_height = draw.box_to_coords(target_lbox['box'])
            x_err = frame_width/2 - xc
            y_err = frame_height/2 - yc

            if x_err < 50 and y_err < 50:
                zoom_command += .1
                if zoom_command >= 1.0:
                    zoom_command = 1.0
                # zoom_command = 1.0

            if box_width >= .7 * frame_width or box_height >= .7 * frame_height:
                zoom_command = 0.0
        else:
            # x_err = 0
            # y_err = 0
            zoom_command -= .1
            if zoom_command <= -1.0:
                zoom_command = -1.0
            # zoom_command = -1.0

        
        zoom_command = checkZeroness(zoom_command)

                
        key = ui.update(frame)

        if key == ord('q'):
            break

        # if zoom_command == 'i':
        #     ptzCam.zoom_in_full()
        # elif zoom_command == 'o':
        #     ptzCam.zoom_out_full()

        ptzCam.move_w_zoom(x_dir, y_dir, zoom_command)

        # x_dir, y_dir, zoom_command = ui.read_mouse()

        def calc_command(err, k):
            command = k * err
            if command >= 1.0:
                command = 1.0
            if command <= -1.0:
                command = -1.0

            return command
                
        x_dir = calc_command(x_err, -.005)
        y_dir = calc_command(y_err, .005)
            
        # print(x_dir, y_dir, zoom_command)

        # if x_dir == 0 and y_dir == 0:
        #     ptzCam.stop()

    cam.release()
    ptzCam.stop()
    ui.clean_up()
