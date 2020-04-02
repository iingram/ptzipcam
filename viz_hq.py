import cv2
import screeninfo

import numpy as np

from dnntools import draw


def create_layout(num_rows, num_columns, column_width, row_height):
    layout = []

    for row in range(num_rows)[::-1]:
        if row % 2 == 0:
            for column in range(num_columns)[::-1]:
                layout.append([column_width * column + column_width,
                               row_height * row + row_height])
        else:
            for column in range(num_columns):
                layout.append([column_width * column + column_width,
                               row_height * row + row_height])
    return layout


class Display():

    def __init__(self, window_name, jump_screens, layout):
        self.window_name = window_name
        self.layout = layout

        cv2.namedWindow(self.window_name,
                        cv2.WINDOW_NORMAL)

        screen_resolutions = screeninfo.get_monitors()
        self.screen_width = screen_resolutions[0].width
        self.screen_height = screen_resolutions[0].height

        if jump_screens:
            print("[NOTICE] Expecting that a second screen is attached.")
            main_screen_width = screen_resolutions[1].width

            cv2.moveWindow(self.window_name,
                           main_screen_width,
                           0)

        cv2.setWindowProperty(self.window_name,
                              cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_FULLSCREEN)

        self.counts = []
        for i in range(len(self.layout)):
            self.counts.append(0)

        self.refresh_canvas()

    def refresh_canvas(self):
        self.canvas = np.zeros((self.screen_height, self.screen_width, 3),
                               np.uint8)

    def draw(self, pics):
        for i in range(len(self.layout)):
            self.counts[i] += 1
            if self.counts[i] > len(pics[i]) - 1:
                self.counts[i] = 0

            if len(pics[i]):
                draw.image_onto_image(self.canvas,
                                      pics[i][self.counts[i]],
                                      self.layout[i])

        cv2.imshow(self.window_name, self.canvas)
        key = cv2.waitKey(30)
        return key

    def release(self):
        cv2.DestroyAllWindows()
