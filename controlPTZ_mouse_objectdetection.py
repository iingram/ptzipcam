#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os

from ptz_camera import PtzCam
from camera import Camera
import ui

from zooSpotter import neuralnetwork as nn
from zooSpotter import draw

IP = "192.168.1.64"   # Camera IP address
PORT = 80           # Port
USER = "admin"         # Username
PASS = "NyalaChow22"        # Password

CONF_THRESHOLD = .2
NMS_THRESHOLD = .4
INPUT_WIDTH = 416
INPUT_HEIGHT = 416

path = '/home/ian/zooSpotter/models/'

model_config =  os.path.join(path, 'yolov3-tiny.cfg')
model_weights =  os.path.join(path, 'yolov3-tiny.weights')
classes_file = os.path.join(path, 'coco.labels')
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
    zoom_command = False
    ptzCam.zoom_out_full()
    
    while True:
        frame = cam.get_frame()
        outs, inferenceTime = network.infer(frame)
        lboxes =  nn.NeuralNetworkHandler.filterBoxes(outs,
                                                      frame,
                                                      CONF_THRESHOLD,
                                                      NMS_THRESHOLD)

        for lbox in lboxes:
            draw.labeledBox(frame, classes, lbox)

        key = ui.update(frame)
     
        if key == ord('q'):
            break
        
        if zoom_command == 'i':
            ptzCam.zoom_in_full()
        elif zoom_command == 'o':
            ptzCam.zoom_out_full()
        
        ptzCam.move(x_dir, y_dir)

        x_dir, y_dir, zoom_command = ui.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    cam.release()
    ptzCam.stop()
    ui.clean_up()
