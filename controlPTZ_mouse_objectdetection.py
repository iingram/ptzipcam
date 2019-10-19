#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os
import yaml
# import time

from ptz_camera import PtzCam
from camera import Camera
import ui

from dnntools import neuralnetwork as nn
from dnntools import draw

with open('configs.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

ORIENTATION = configs['ORIENTATION']
    
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']        
PASS = configs['PASS']

CONF_THRESHOLD = configs['CONF_THRESHOLD']
NMS_THRESHOLD = configs['NMS_THRESHOLD']
INPUT_WIDTH = configs['INPUT_WIDTH']
INPUT_HEIGHT = configs['INPUT_HEIGHT']

# path = '/home/ian/zoo_spotter/models/'
path = configs['MODEL_PATH']
model_config =  os.path.join(path, 'yolov3-tiny.cfg')
model_weights =  os.path.join(path, 'yolov3-tiny.weights')
classes_file = os.path.join(path, 'coco.labels')
classes = nn.read_classes_from_file(classes_file)

if __name__ == '__main__':
    ptz_cam = PtzCam(IP, PORT, USER, PASS)
    cam = Camera()

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)

    window_name = 'Control PTZ Camera with mouse'
    uih = ui.UI_Handler(frame, window_name)

    network = nn.ObjectDetectorHandler(model_config,
                                       model_weights,
                                       INPUT_WIDTH,
                                       INPUT_HEIGHT)

    x_dir = 0
    y_dir = 0
    zoom_command = False
    ptz_cam.zoom_out_full()
    
    while True:
        # time.sleep(1)
        raw_frame = cam.get_frame()
        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        outs, inference_time = network.infer(frame)
        lboxes =  nn.ObjectDetectorHandler.filter_boxes(outs,
                                                        frame,
                                                        CONF_THRESHOLD,
                                                        NMS_THRESHOLD)

        for lbox in lboxes:
            draw.labeledBox(frame, classes, lbox)

        key = uih.update(frame)
     
        if key == ord('q'):
            break
        
        if zoom_command == 'i':
            ptz_cam.zoom_in_full()
        elif zoom_command == 'o':
            ptz_cam.zoom_out_full()
        
        if ORIENTATION=='left':
            ptz_cam.move(y_dir, -x_dir)
        elif ORIENTATION=='down':
            ptz_cam.move(-x_dir, -y_dir)
        else:
            ptz_cam.move(x_dir, y_dir)

        x_dir, y_dir, zoom_command = uih.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptz_cam.stop()

    cam.release()
    ptz_cam.stop()
    uih.clean_up()
