from onvif import ONVIFCamera


class PtzCam():

    def __init__(self,
                 ip = '192.168.1.64',
                 port = '80',
                 user = 'admin',
                 pword = 'NyalaChow22'):

        mycam = ONVIFCamera(ip, port, user, pword)
        media = mycam.create_media_service()
        self.ptz = mycam.create_ptz_service()
        media_profile = media.GetProfiles()[0]

        self.moverequest = self.ptz.create_type('ContinuousMove')
        self.moverequest.ProfileToken = media_profile.token
        # if self.moverequest.Velocity is None:
            # self.moverequest.Velocity = {'PanTilt': {'x': -1, 'y': -1},
            #                              'Zoom': {'x': 0.0}}

        self.moverequest.Velocity = {'PanTilt': {'x': -1, 'y': 1},
                                     'Zoom': {'x': 0.0}}

    def move(self, x_dir, y_dir):
        self.moverequest.Velocity = {'PanTilt': {'x': x_dir, 'y': y_dir},
                                     'Zoom': {'x': 0.0}}
        self.ptz.ContinuousMove(self.moverequest)

    def stop(self):
        self.ptz.Stop({'ProfileToken': self.moverequest.ProfileToken})
