"""Utility for playing back the frames in an image series created by
various tools in this package.

Use second command line argument to "fast forward" by skipping that
number of frames for every render.

"""

import os
import argparse

import cv2
import pandas as pd

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

args = ap.parse_args()

csv_filename = args.filename
stride = int(args.stride)
msecs_per_frame = int(1000 * (1.0/int(args.rate)))
print(msecs_per_frame)
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
        print(filename)
        img = cv2.imread(filename)

        cv2.imshow('hoot', img)
        key = cv2.waitKey(msecs_per_frame)
        if key == ord('q'):
            break

cv2.destroyAllWindows()
# sys.exit()
