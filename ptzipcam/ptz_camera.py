import time

from onvif import ONVIFCamera


def _checkZeroness(number):
    """Checks if a number is very close to zero (within a window) and if
it is makes it less close by placing it at the edge of that window.

    Parameters
    ----------

    number : float

        A number to be checked for closeness to zero

    Returns
    -------

    number : float

        The "fixed" number

    """
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
        media_service = mycam.create_media_service()
        self.ptz_service = mycam.create_ptz_service()
        self.imaging_service = mycam.create_imaging_service()

        # on hikvision cameras there have been 3 profiles: one for each stream
        self.media_profile = media_service.GetProfiles()[0]

        self.video_source = media_service.GetVideoSources()[0]

        # self.moverequest = self.ptz.create_type('ContinuousMove')
        # self.moverequest.ProfileToken = media_profile.token
        # # if self.moverequest.Velocity is None:
        #     # self.moverequest.Velocity = {'PanTilt': {'x': -1, 'y': -1},
        #     #                              'Zoom': {'x': 0.0}}

        # self.moverequest.Velocity = {'PanTilt': {'x': -1, 'y': 1},
        #                              'Zoom': {'x': 0.0}}

    def focus_out(self):
        focus_request = self.imaging_service.create_type('Move')
        focus_request.VideoSourceToken = self.video_source.token
        focus_request.Focus = {'Continuous': {'Speed': 0.1}}
        self.imaging_service.Move(focus_request)

    def focus_in(self):
        focus_request = self.imaging_service.create_type('Move')
        focus_request.VideoSourceToken = self.video_source.token
        focus_request.Focus = {'Continuous': {'Speed': -0.1}}
        self.imaging_service.Move(focus_request)

    def focus_stop(self):
        self.imaging_service.Stop(self.video_source.token)

    def move(self, x_velocity, y_velocity):
        move_request = self.ptz_service.create_type('ContinuousMove')
        move_request.ProfileToken = self.media_profile.token
        move_request.Velocity = {'PanTilt': {'x': x_velocity, 'y': y_velocity},
                                 'Zoom': {'x': 0.0}}
        self.ptz_service.ContinuousMove(move_request)

    def move_w_zoom(self, x_velocity, y_velocity, zoom_command):
        x_velocity = float(_checkZeroness(x_velocity))
        y_velocity = float(_checkZeroness(y_velocity))
        zoom_command = _checkZeroness(zoom_command)

        move_request = self.ptz_service.create_type('ContinuousMove')
        move_request.ProfileToken = self.media_profile.token
        move_request.Velocity = {'PanTilt': {'x': x_velocity, 'y': y_velocity},
                                 'Zoom': {'x': zoom_command}}
        self.ptz_service.ContinuousMove(move_request)

    def _prep_abs_move(self):
        move_request = self.ptz_service.create_type('AbsoluteMove')
        move_request.ProfileToken = self.media_profile.token
        if move_request.Position is None:
            move_request.Position = self.ptz_service.GetStatus({'ProfileToken': self.media_profile.token}).Position
            move_request.Speed = self.media_profile.PTZConfiguration.DefaultPTZSpeed

        return move_request

    def get_position(self):
        move_request = self.ptz_service.create_type('AbsoluteMove')
        move_request.ProfileToken = self.media_profile.token
        position = self.ptz_service.GetStatus({'ProfileToken': self.media_profile.token}).Position

        # x = pan, y = tilt
        return (position['PanTilt']['x'],
                position['PanTilt']['y'],
                position['Zoom']['x'])

    def absmove(self, x_pos, y_pos):
        move_request = self._prep_abs_move()
        move_request.Position.PanTilt.x = x_pos
        move_request.Position.PanTilt.y = y_pos
        self.ptz_service.AbsoluteMove(move_request)

    def absmove_w_zoom(self, pan_pos, tilt_pos, zoom_pos):
        """Move PTZ camera to an absolute pan, tilt, zoom state.

        Parameters
        ----------
        pan_pos : float

            The desired pan position expressed as a value in accepted
            range (often -1.0 to 1.0) that maps to the actual range of
            the camera (e.g. 0-350 degrees or 0-360 degrees).

        tilt_pos : float

            The desired tilt position expressed as a value in accepted
            range (often -1.0 to 1.0) that maps to the actual range of
            the camera (e.g. 0-90 degrees or -5 to 90 degrees)

        zoom_pos : float

            The desired zoom "position" expressed as a value in
            accepted range (often 0.0 to 1.0) that maps to the actual
            zoom range of the camera.

        Returns
        -------
        None

        """
        zoom_pos = _checkZeroness(zoom_pos)
        pan_pos = _checkZeroness(pan_pos)
        tilt_pos = _checkZeroness(tilt_pos)

        move_request = self._prep_abs_move()
        move_request.Position.PanTilt.x = pan_pos
        move_request.Position.PanTilt.y = tilt_pos
        move_request.Position.Zoom.x = zoom_pos
        self.ptz_service.AbsoluteMove(move_request)

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
        move_request = self._prep_abs_move()
        move_request.Position.Zoom.x = 0.0
        self.ptz_service.AbsoluteMove(move_request)

    def zoom_in_full(self):
        move_request = self._prep_abs_move()
        move_request.Position.Zoom.x = 1.0
        self.ptz_service.AbsoluteMove(move_request)

    def zoom(self, zoom_command):
        zoom_command = _checkZeroness(zoom_command)

        move_request = self._prep_abs_move()
        move_request.Position.Zoom.x = zoom_command
        self.ptz_service.AbsoluteMove(move_request)

    def stop(self):
        move_request = self._prep_abs_move()
        self.ptz_service.Stop({'ProfileToken': move_request.ProfileToken})
