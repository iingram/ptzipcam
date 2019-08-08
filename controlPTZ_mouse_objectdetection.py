#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os
import yaml
import argparse

from ptz_camera import PtzCam
from camera import Camera
import ui

from zooSpotter import neuralnetwork as nn
from zooSpotter import draw


ap = argparse.ArgumentParser()

ap.add_argument('-s',
                '--sideways',
                action='store_true',
                help='set if camera is oriented sideways')

ap.add_argument('-u',
                '--upside_down',
                action='store_true',
                help='set if camera upside-down')

args = ap.parse_args()

SIDEWAYS = args.sideways
UPSIDE_DOWN = args.upside_down

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

path = '/home/ian/zooSpotter/models/'

model_config =  os.path.join(path, 'yolov3-tiny.cfg')
model_weights =  os.path.join(path, 'yolov3-tiny.weights')
classes_file = os.path.join(path, 'coco.labels')
classes = nn.read_classes_from_file(classes_file)

if __name__ == '__main__':
    ptzCam = PtzCam(IP, PORT, USER, PASS)
    cam = Camera()

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, SIDEWAYS, UPSIDE_DOWN)

    window_name = 'Control PTZ Camera with mouse'
    uih = ui.UI_Handler(frame, window_name)

    network = nn.NeuralNetworkHandler(model_config,
                                      model_weights,
                                      INPUT_WIDTH,
                                      INPUT_HEIGHT)

    x_dir = 0
    y_dir = 0
    zoom_command = False
    ptzCam.zoom_out_full()
    
    while True:
        raw_frame = cam.get_frame()
        raw_frame = ui.orient_frame(raw_frame, SIDEWAYS, UPSIDE_DOWN)
        frame = raw_frame.copy()

        outs, inferenceTime = network.infer(frame)
        lboxes =  nn.NeuralNetworkHandler.filterBoxes(outs,
                                                      frame,
                                                      CONF_THRESHOLD,
                                                      NMS_THRESHOLD)

        for lbox in lboxes:
            draw.labeledBox(frame, classes, lbox)

        key = uih.update(frame)
     
        if key == ord('q'):
            break
        
        if zoom_command == 'i':
            ptzCam.zoom_in_full()
        elif zoom_command == 'o':
            ptzCam.zoom_out_full()
        
        if SIDEWAYS:
            ptzCam.move(y_dir, -x_dir)
        elif UPSIDE_DOWN:
            ptzCam.move(-x_dir, -y_dir)
        else:
            ptzCam.move(x_dir, y_dir)

        x_dir, y_dir, zoom_command = uih.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    cam.release()
    ptzCam.stop()
    uih.clean_up()
