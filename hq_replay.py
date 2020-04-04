import argparse

import viz_hq
import io_hq

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
viz_hq.print_layout_geometry(NUM_ROWS, NUM_COLS)

display = viz_hq.Display("HQ Replay", JUMP_SCREENS, layout)

path = '/home/ian/2020-04-01_biodiversity_reserve/images'
pics = io_hq.read_in_pics(path, args.csv_file, layout, 320)
        
while True:
    key = display.draw(pics)
    if key == ord('q'):
        break
    elif key == ord('s'):
        display.frame_duration = 1000
    elif key == ord('f'):
        display.frame_duration = 30
        
