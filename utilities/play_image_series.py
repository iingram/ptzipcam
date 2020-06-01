import sys
import os

import cv2
import pandas as pd

csv_filename = sys.argv[1]
main_timestamp = csv_filename.split('.')[0]

df = pd.read_csv(csv_filename)

base_path = os.path.split(csv_filename)[0]
base_path = os.path.join(base_path, main_timestamp + '_images') 

for index, row in df.iterrows():
    filename = os.path.join(base_path, row.IMAGE_FILE)
    print(filename)
    img = cv2.imread(filename)
    
    cv2.imshow('hoot', img)
    key = cv2.waitKey(30)
    if key == ord('q'):
        break
        
cv2.destroyAllWindows()
# sys.exit()



