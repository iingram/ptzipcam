import os
import argparse

import imutils
import cv2
import pandas as pd

import viz_hq

parser = argparse.ArgumentParser()
parser.add_argument('-c',
                    '--csv_file',
                    required=True,
                    help='CSV file containing image names and metadata')
args = parser.parse_args()

JUMP_SCREENS = False
NUM_COLS = 10
NUM_ROWS = 7
COL_WIDTH = 330
ROW_HEIGHT = 250

layout = viz_hq.create_layout(NUM_ROWS, NUM_COLS, COL_WIDTH, ROW_HEIGHT, upside_down=True)
print('Grid: ' + str(NUM_COLS) + 'x' + str(NUM_ROWS))
WINDOW_NAME = "HQ Replay"
display = viz_hq.Display(WINDOW_NAME, JUMP_SCREENS, layout)


def read_in_pics(path, csv_file, layout, image_width):
    pics = viz_hq.init_pics(layout)

    df = pd.read_csv(csv_file)

    for index, row in df.iterrows():
        full_path =  os.path.join(path,
                                  row['IMAGE_FILE'])

        img = cv2.imread(full_path)
        img = imutils.resize(img, image_width)
        pics[index % len(layout)].append(img)
                       
    return pics


path = '/home/ian/2020-04-01_biodiversity_reserve/images'
pics = read_in_pics(path, args.csv_file, layout, 320)
        
while True:
    # display.refresh_canvas()

    key = display.draw(pics)
    if key == ord('q'):
        break
