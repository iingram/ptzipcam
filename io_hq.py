import os

import cv2
import imutils

import pandas as pd

import viz_hq

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
