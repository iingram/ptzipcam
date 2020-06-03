"""Utility for playing back the frames in an image series created by
various tools in this package.  

Use second command line argument to "fast forward" by skipping that
number of frames for every render.

"""

import sys
import os

import cv2
import pandas as pd

csv_filename = sys.argv[1]
skip_frames = int(sys.argv[2])
main_timestamp = csv_filename.split('.')[0]

df = pd.read_csv(csv_filename)

base_path = os.path.split(csv_filename)[0]
base_path = os.path.join(base_path, main_timestamp + '_images')

count = -1
for index, row in df.iterrows():
    count += 1
    if count % skip_frames == 0:
        count = 0
        filename = os.path.join(base_path, row.IMAGE_FILE)
        print(filename)
        img = cv2.imread(filename)

        cv2.imshow('hoot', img)
        key = cv2.waitKey(30)
        if key == ord('q'):
            break

cv2.destroyAllWindows()
# sys.exit()
