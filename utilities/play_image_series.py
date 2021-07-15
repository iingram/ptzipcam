#!/usr/bin/env python
"""Playback frames from a run

Utility for playing back the frames in an image series created by
various tools in the ptzipcam package.

Use second command line argument to "fast forward" by skipping that
number of frames for every render.
"""
import os
import argparse

import cv2
import pandas as pd

from dnntools import draw

ap = argparse.ArgumentParser()

ap.add_argument('filename',
                help='CSV file of image series.')
ap.add_argument('-s',
                '--stride',
                default=1,
                help='Stride through playback (to fast-forward)')
ap.add_argument('-r',
                '--rate',
                default=30,
                help="Desired frames per second (program only approximates)")
ap.add_argument('-b',
                '--box',
                action='store_true',
                help="Toggle drawing boxes on frames")
ap.add_argument('-o',
                '--output_path',
                help="Path to store output frames")

print("[INFO]: don't forget that you can set stride and fps on cli")

args = ap.parse_args()

csv_filename = args.filename
stride = int(args.stride)
msecs_per_frame = int(1000 * (1.0/int(args.rate)))
print('[INFO] FPS results in '
      '{} milliseconds per frame.'.format(msecs_per_frame))
main_timestamp = csv_filename.split('.')[0]

df = pd.read_csv(csv_filename)

base_path = os.path.split(csv_filename)[0]
base_path = os.path.join(base_path, main_timestamp + '_images')

count = -1
for index, row in df.iterrows():
    count += 1
    if count % stride == 0:
        count = 0
        filename = os.path.join(base_path, row.IMAGE_FILE)
        # print(filename)
        img = cv2.imread(filename)
        if(args.box
           and row.CLASS != 'nothing detected'
           and row.CLASS != 'n/a: start-up frame'):
            lbox = {}
            lbox['box'] = (int(row.X),
                           int(row.Y),
                           int(row.W),
                           int(row.H))
            lbox['class_name'] = row.CLASS
            lbox['confidence'] = int(row.SCORE)

            draw.labeled_box(img,
                             None,
                             lbox,
                             thickness=3,
                             show_score=False,
                             color=(4, 139, 229))  # 229, 171, 4

        if args.output_path:
            just_name = os.path.split(filename)[1]
            filename = os.path.join(args.output_path, just_name)
            cv2.imwrite(filename, img)

        cv2.imshow('Playback', img)
        key = cv2.waitKey(msecs_per_frame)
        if key == ord('q'):
            break

cv2.destroyAllWindows()
# sys.exit()
