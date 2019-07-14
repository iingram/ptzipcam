#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os
import yaml

from ptz_camera import PtzCam
from camera import Camera
import ui

from zooSpotter import neuralnetwork as nn
from zooSpotter import draw

with open('configs.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']        
PASS = configs['PASS']

CONF_THRESHOLD = configs['CONF_THRESHOLD']
NMS_THRESHOLD = configs['NMS_THRESHOLD']
INPUT_WIDTH = configs['INPUT_WIDTH']
INPUT_HEIGHT = configs['INPUT_HEIGHT']

MODEL_PATH = configs['MODEL_PATH']

model_config =  os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
model_weights =  os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
classes_file = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
classes = nn.read_classes_from_file(classes_file)

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
    zoom_command = None
    ptzCam.zoom_out_full()

    x_err = 0

    while True:
        frame = cam.get_frame()
        outs, inferenceTime = network.infer(frame)
        lboxes =  nn.NeuralNetworkHandler.filterBoxes(outs,
                                                      frame,
                                                      CONF_THRESHOLD,
                                                      NMS_THRESHOLD)

        highest_person_confidence = 0
        highest_confidence_lbox = None
        for lbox in lboxes:
            if classes[lbox['classId']] == 'person':
                if lbox['confidence'] > highest_person_confidence:
                    highest_person_confidence = lbox['confidence']
                    highest_confidence_lbox = lbox

        if highest_confidence_lbox:
            draw.labeledBox(frame, classes, lbox)
            xc, yc = draw.box_to_coords(lbox['box'], return_kind='center')
            x_err = frame.shape[1]/2 - xc
                # print(frame.shape[1], xc, x_err)
                # if x_err < 50:
                #     zoom_command = 'i'
        # else:
        #     zoom_command = 'o'
        
        
        key = ui.update(frame)
     
        if key == ord('q'):
            break
        
        if zoom_command == 'i':
            ptzCam.zoom_in_full()
        elif zoom_command == 'o':
            ptzCam.zoom_out_full()
        
        ptzCam.move(x_dir, y_dir)

        # x_dir, y_dir, zoom_command = ui.read_mouse()

        x_dir = - .005 * x_err
        if x_dir >= 1.0:
            x_dir = 1.0
        if x_dir <= -1.0:
            x_dir = -1.0
        
        print(x_dir)

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    cam.release()
    ptzCam.stop()
    ui.clean_up()
