from onvif import ONVIFCamera


class PtzCam():
    """Class for controlling the pan-tilt-zoom of an ONVIF-compliant IP
    camera that has PTZ capability.

    """
    def __init__(self,
                 ip='192.168.1.64',
                 port='80',
                 user='admin',
                 pword='NyalaChow22'):

        mycam = ONVIFCamera(ip, port, user, pword)
        media = mycam.create_media_service()
        self.ptz = mycam.create_ptz_service()
        self.media_profile = media.GetProfiles()[0]

        # self.moverequest = self.ptz.create_type('ContinuousMove')
        # self.moverequest.ProfileToken = media_profile.token
        # # if self.moverequest.Velocity is None:
        #     # self.moverequest.Velocity = {'PanTilt': {'x': -1, 'y': -1},
        #     #                              'Zoom': {'x': 0.0}}

        # self.moverequest.Velocity = {'PanTilt': {'x': -1, 'y': 1},
        #                              'Zoom': {'x': 0.0}}

    def move(self, x_dir, y_dir):
        self.moverequest = self.ptz.create_type('ContinuousMove')
        self.moverequest.ProfileToken = self.media_profile.token
        self.moverequest.Velocity = {'PanTilt': {'x': x_dir, 'y': y_dir},
                                     'Zoom': {'x': 0.0}}
        self.ptz.ContinuousMove(self.moverequest)

    def _prep_abs_move(self):
        self.moverequest = self.ptz.create_type('AbsoluteMove')
        self.moverequest.ProfileToken = self.media_profile.token
        if self.moverequest.Position is None:
            self.moverequest.Position = self.ptz.GetStatus({'ProfileToken': self.media_profile.token}).Position
            self.moverequest.Speed = self.media_profile.PTZConfiguration.DefaultPTZSpeed

    def absmove(self, x_pos, y_pos):
        self._prep_abs_move()
        self.moverequest.Position.PanTilt.x = x_pos
        self.moverequest.Position.PanTilt.y = y_pos
        self.ptz.AbsoluteMove(self.moverequest)

    def zoom_out_full(self):
        self._prep_abs_move()
        self.moverequest.Position.Zoom.x = 0.0
        self.ptz.AbsoluteMove(self.moverequest)

    def zoom_in_full(self):
        self._prep_abs_move()
        self.moverequest.Position.Zoom.x = 1.0
        self.ptz.AbsoluteMove(self.moverequest)

    def stop(self):
        self._prep_abs_move()
        self.ptz.Stop({'ProfileToken': self.moverequest.ProfileToken})
