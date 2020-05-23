import time

from onvif import ONVIFCamera


def _checkZeroness(number):
    e = .001

    if number < e and number > -e:
        return 0
    else:
        return number


class MotorController():

    def __init__(self, pid_gains, orientation):
        self.pid_gains = pid_gains
        self.orientation = orientation

    def _calc_command(self, err, k):
        command = k * err
        if command >= 1.0:
            command = 1.0
        if command <= -1.0:
            command = -1.0

        # if command > -0.1 and command < 0.1:
        #     command = 0.0

        return command
        
    def run(self, x_err, y_err):
        if self.orientation == 'down':
            x_err = -x_err
            y_err = -y_err

        x_velocity = self._calc_command(x_err, self.pid_gains[0])
        y_velocity = self._calc_command(y_err, self.pid_gains[1])

        return (x_velocity, y_velocity)
    

    

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

    def move(self, x_velocity, y_velocity):
        self.moverequest = self.ptz.create_type('ContinuousMove')
        self.moverequest.ProfileToken = self.media_profile.token
        self.moverequest.Velocity = {'PanTilt': {'x': x_velocity, 'y': y_velocity},
                                     'Zoom': {'x': 0.0}}
        self.ptz.ContinuousMove(self.moverequest)

    def move_w_zoom(self, x_velocity, y_velocity, zoom_command):
        x_velocity = float(_checkZeroness(x_velocity))
        y_velocity = float(_checkZeroness(y_velocity))
        zoom_command = _checkZeroness(zoom_command)

        self.moverequest = self.ptz.create_type('ContinuousMove')
        self.moverequest.ProfileToken = self.media_profile.token
        self.moverequest.Velocity = {'PanTilt': {'x': x_velocity, 'y': y_velocity},
                                     'Zoom': {'x': zoom_command}}
        self.ptz.ContinuousMove(self.moverequest)

    def _prep_abs_move(self):
        self.moverequest = self.ptz.create_type('AbsoluteMove')
        self.moverequest.ProfileToken = self.media_profile.token
        if self.moverequest.Position is None:
            self.moverequest.Position = self.ptz.GetStatus({'ProfileToken': self.media_profile.token}).Position
            self.moverequest.Speed = self.media_profile.PTZConfiguration.DefaultPTZSpeed

    def get_position(self):
        self.moverequest = self.ptz.create_type('AbsoluteMove')
        self.moverequest.ProfileToken = self.media_profile.token
        position = self.ptz.GetStatus({'ProfileToken': self.media_profile.token}).Position

        # x = pan, y = tilt
        return position['PanTilt']['x'], position['PanTilt']['y'], position['Zoom']['x']

    def absmove(self, x_pos, y_pos):
        self._prep_abs_move()
        self.moverequest.Position.PanTilt.x = x_pos
        self.moverequest.Position.PanTilt.y = y_pos
        self.ptz.AbsoluteMove(self.moverequest)

    def absmove_w_zoom(self, pan_pos, tilt_pos, zoom_pos):
        zoom_pos = _checkZeroness(zoom_pos)
        pan_pos = _checkZeroness(pan_pos)
        tilt_pos = _checkZeroness(tilt_pos)
        self._prep_abs_move()
        self.moverequest.Position.PanTilt.x = pan_pos
        self.moverequest.Position.PanTilt.y = tilt_pos
        self.moverequest.Position.Zoom.x = zoom_pos
        self.ptz.AbsoluteMove(self.moverequest)

    def _wait_for_done(self, pan_goal, tilt_goal, zoom_goal, close_enough=.01):
        """Note: zoom_goal finishing not implemented

        """
        pan, tilt, zoom = self.get_position()
        while (pan >= pan_goal + close_enough
               or pan <= pan_goal - close_enough
               or tilt >= tilt_goal + close_enough
               or tilt <= tilt_goal - close_enough):
            time.sleep(.1)
            pan, tilt, zoom = self.get_position()


    def absmove_w_zoom_waitfordone(self,
                                   pan_pos,
                                   tilt_pos,
                                   zoom_pos,
                                   close_enough=.01):
        self.absmove_w_zoom(pan_pos, tilt_pos, zoom_pos)
        self._wait_for_done(pan_pos, tilt_pos, zoom_pos, close_enough)

        
    def zoom_out_full(self):
        self._prep_abs_move()
        self.moverequest.Position.Zoom.x = 0.0
        self.ptz.AbsoluteMove(self.moverequest)

    def zoom_in_full(self):
        self._prep_abs_move()
        self.moverequest.Position.Zoom.x = 1.0
        self.ptz.AbsoluteMove(self.moverequest)

    def zoom(self, zoom_command):
        zoom_command = _checkZeroness(zoom_command)
        self._prep_abs_move()
        self.moverequest.Position.Zoom.x = zoom_command
        self.ptz.AbsoluteMove(self.moverequest)

    def stop(self):
        self._prep_abs_move()
        self.ptz.Stop({'ProfileToken': self.moverequest.ProfileToken})
