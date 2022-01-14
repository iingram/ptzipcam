import argparse

from viztools.visualization import create_layout, GridDisplay, print_layout_geometry

import io_hq

parser = argparse.ArgumentParser()
parser.add_argument('-c',
                    '--csv_file',
                    required=True,
                    help='CSV file containing image names and metadata')
parser.add_argument('-b',
                    '--base_path',
                    required=True,
                    help='Base path of image file location')
args = parser.parse_args()

JUMP_SCREENS = False
NUM_COLS = 10
NUM_ROWS = 7
COL_WIDTH = 330
ROW_HEIGHT = 250

layout = create_layout(NUM_ROWS,
                       NUM_COLS,
                       COL_WIDTH,
                       ROW_HEIGHT,
                       upside_down=False)
print_layout_geometry(NUM_ROWS, NUM_COLS)

display = GridDisplay("HQ Replay", JUMP_SCREENS, layout)

pics = io_hq.read_in_pics(args.base_path,
                          args.csv_file,
                          layout,
                          320)


while True:
    key = display.draw(pics)
    if key == ord('q'):
        break
    elif key == ord('s'):
        display.frame_duration = 1000
    elif key == ord('f'):
        display.frame_duration = 30
