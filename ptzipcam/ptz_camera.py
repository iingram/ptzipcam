"""Tools for control of pan-tilt-zoom functionality of PTZ IP camera

"""
import logging
import time

import numpy as np
from onvif import ONVIFCamera

from camml import draw

log = logging.getLogger(__name__)


def _check_zeroness(number):
    """Almost-zero check

    Checks if a number is very close to zero (within a window) and if
    it is makes it less close by placing it at the edge of that
    window.

    Parameters
    ----------
    number : float
        A number to be checked for closeness to zero

    Returns
    -------
    number : float
        The "fixed" number

    """
    eps = .001

    if -eps < number < eps:
        number = 0

    return number


class MotorController():
    """Base class for motor controllers

    """
    # pylint: disable='too-few-public-methods'

    def __init__(self,
                 pid_gains,
                 orientation,
                 example_frame):
        """Constructor for MotorController class

        """

        self.pid_gains = pid_gains
        self.orientation = orientation

        self.frame_width = example_frame.shape[1]
        self.frame_height = example_frame.shape[0]

        self.total_frame_pixels = self.frame_width * self.frame_height

    def _calc_errors(self,
                     target_lbox):
        """Calculate errors from box coordinates

        Given a labeled box that is the bounding box of a detected
        target, this function calculates an error for each of x and y
        (pan and tilt) based on the offset of the centroid of the
        bounding box from the center of the frame.

        """
        if target_lbox:
            x_c, y_c = draw.box_to_coords(target_lbox['box'],
                                          return_kind='center')
            ret = draw.box_to_coords(target_lbox['box'])
            self.box_x, self.box_y, self.box_width, self.box_height = ret
            x_err = self.frame_width/2 - x_c
            y_err = self.frame_height/2 - y_c

            # normalize errors
            x_err = x_err/self.frame_width
            y_err = y_err/self.frame_height
        else:
            x_err = 0.0
            y_err = 0.0

        return x_err, y_err

    def update(self, target_lbox, zoom_command):
        """Update the camera commands

        Generates commands for pan, tilt, and zoom given the current
        target_lbox (which is None when no detection) and the current
        zoom_command.

        Parameters
        ----------
        target_lbox :

        zoom_command : float
            Current zoom_command

        Returns
        -------
        x_velocity :

        y_velocity :

        zoom_command :

        """
        errors = self._calc_errors(target_lbox)
        x_err, y_err = errors

        if self.orientation == 'down':
            x_err = -x_err
            y_err = -y_err

        x_velocity = self._calc_command(x_err, self.pid_gains[0])
        y_velocity = self._calc_command(y_err, self.pid_gains[1])
        zoom_command = self._calc_zoom_command(target_lbox,
                                               x_err,
                                               y_err,
                                               zoom_command)

        log.debug('x_err: %.2f || y_err: %.2f', x_err, y_err)
        log.debug('x_vel: %.2f || y_vel: %.2f', x_velocity, y_velocity)
        log.debug('zoom_command: %.2f', zoom_command)

        return (x_velocity, y_velocity, zoom_command)

    def _ensure_command_in_bounds(self, command):
        """Util to force command is within necessary bounds

        """
        if command >= 1.0:
            command = 1.0
        if command <= -1.0:
            command = -1.0

        return command

    def _calc_command(self, err, k):
        """Implements actual controller math

        This basic implementation in the base class is a mere
        proportional controller.  If need PI, PID, or such, this
        method should be replaced in the child class.  It is not
        currently imagined that controllers outside the PID space will
        be pursued.

        """
        command = k * err
        command = self._ensure_command_in_bounds(command)
        return command

    def _calc_zoom_command(self, target_lbox, x_err, y_err, zoom_command):
        """Calculate the next zoom command

        Not implemented in the base class. But should be implemented
        to effect zoom control based on position/size of target_lbox.

        """
        raise NotImplementedError


class CalmMotorController(MotorController):
    """MotorController with calm movements/behaviors

    In certain instances, the desire is not for rapid and exacting
    tracking but for tracking that doesn't distract from the scene
    through quick movements and jitteriness.  This subclass is
    intended to be that sort of calm tracker.

    """

    def __init__(self,
                 pid_gains,
                 orientation,
                 example_frame):

        super().__init__(pid_gains,
                         orientation,
                         example_frame)

        self.zoom_stop_ratio = .6
        self.stop_range = .1

    def _calc_command(self, err, k):
        """Override controller command method

        The meat here is that the controller stops moving axis under
        control if error is inside of some range.  This range is
        currently hardcoded but maybe should be given as an argument
        to the constructor.

        """

        if np.abs(err) < self.stop_range:
            command = 0
        else:
            command = k * err

        command = self._ensure_command_in_bounds(command)

        return command

    def _calc_zoom_command(self, target_lbox, x_err, y_err, zoom_command):
        """Calculate the zoom command give pan/tilt errors

        This is where most of the behavior of the tracking is
        implemented.

        """

        if (x_err <= 0.5 and y_err <= 0.5
           and target_lbox):
            target_bb_pixels = self.box_width * self.box_height

            box_ratio = target_bb_pixels / self.total_frame_pixels
            log.debug('Ratio of box to whole %.2f', box_ratio)

            if box_ratio < .3:
                zoom_command = 1.0
            else:
                zoom_command = 0.0

            ratio = self.zoom_stop_ratio
            spans_much_width = self.box_width >= ratio * self.frame_width
            spans_much_height = self.box_height >= ratio * self.frame_height
            if spans_much_width or spans_much_height:
                zoom_command = 0.0

            margin = 20
            if ((self.box_y + self.box_height) >= (self.frame_height - margin)
               or (self.box_y <= margin)):
                zoom_command = -1.0

        return zoom_command


class TwitchyMotorController(MotorController):

    def __init__(self,
                 pid_gains,
                 orientation,
                 example_frame):

        super().__init__(pid_gains,
                         orientation,
                         example_frame)

        self.zoom_stop_ratio = .7

    def _calc_zoom_command(self, target_lbox, x_err, y_err, zoom_command):
        """Calculate the zoom command give pan/tilt errors

        """
        if x_err != 0.0 and y_err != 0.0:
            target_bb_pixels = self.box_width * self.box_height

            # ratio of bb pixels over whole frame pixels is below a
            # threshold then zoom
            ratio = target_bb_pixels / self.total_frame_pixels
            error = 1 - ratio
            zoom_command = 0.05 * error

            # stop zoom if either dimension of bounding box is
            l_ratio = self.zoom_stop_ratio  # length ratio
            spans_much_width = self.box_width >= l_ratio * self.frame_width
            spans_much_height = self.box_height >= l_ratio * self.frame_height
            if spans_much_width or spans_much_height:
                zoom_command = -0.1

            # margin = 100
            # if((self.box_y + self.box_height) >= (self.frame_height - margin)
            #    or (self.box_y <= margin)):
            #     zoom_command = 0.0
        else:
            zoom_command = 0.0

        return zoom_command


class BouncyZoomMotorController(MotorController):

    def __init__(self,
                 pid_gains,
                 orientation,
                 example_frame):

        super().__init__(pid_gains,
                         orientation,
                         example_frame)

        self.zoom_stop_ratio = .7

    def _calc_zoom_command(self, target_lbox, x_err, y_err, zoom_command):
        """Calculate the zoom command give pan/tilt errors

        """
        if x_err != 0.0 and y_err != 0.0:
            target_bb_pixels = self.box_width * self.box_height

            # ratio of bb pixels over whole frame pixels is below a
            # threshold then zoom
            ratio = target_bb_pixels / self.total_frame_pixels
            if ratio < .1:
                zoom_command = 0.01
            elif ratio > .3:
                zoom_command = -0.01
            else:
                zoom_command = 0.0
        else:
            zoom_command = 0.0

        return zoom_command


class PtzCam():
    """Class to control PTZ on ONVIF-compliant PTZ IP Camera

    Allows control of the pan, tilt, and zoom of an ONVIF-compliant IP
    camera that has PTZ capability.

    """
    def __init__(self,
                 ip_address=None,
                 port='80',
                 user=None,
                 pword=None):
        """ PtzCam constructor

        Parameters
        ----------
        ip_address : str
           The IP address of the camera to connect to.
        port : str
           ONVIF port on the camera. This is usually 80
        user : str
           Valid username of account on the IP camera being connected to.
        pword : str
           Password for the account on the IP camera.

        """

        mycam = ONVIFCamera(ip_address, port, user, pword)
        media_service = mycam.create_media_service()
        self.ptz_service = mycam.create_ptz_service()
        self.imaging_service = mycam.create_imaging_service()

        # on hikvision cameras there have been 3 profiles: one for each stream
        self.media_profile = media_service.GetProfiles()[0]

        self.video_source = media_service.GetVideoSources()[0]

        self.pan_bounds = [-1.0, 1.0]
        self.tilt_bounds = [-1.0, 1.0]
        self.zoom_bounds = [0.0, 1.0]

        vst = {'VideoSourceToken': self.video_source.token}
        self.imaging_settings = self.imaging_service.GetImagingSettings(vst)

        min_iris = self.imaging_settings.Exposure.MinIris,
        max_iris = self.imaging_settings.Exposure.MaxIris,
        self.iris_bounds = [min_iris,
                            max_iris]

        min_exposure_time = self.imaging_settings.Exposure.MinExposureTime
        max_exposure_time = self.imaging_settings.Exposure.MaxExposureTime
        self.exposure_time_bounds = [min_exposure_time,
                                     max_exposure_time]

        # self.moverequest = self.ptz.create_type('ContinuousMove')
        # self.moverequest.ProfileToken = media_profile.token
        # # if self.moverequest.Velocity is None:
        #     # self.moverequest.Velocity = {'PanTilt': {'x': -1, 'y': -1},
        #     #                              'Zoom': {'x': 0.0}}

        # self.moverequest.Velocity = {'PanTilt': {'x': -1, 'y': 1},
        #                              'Zoom': {'x': 0.0}}

    def __del__(self):
        log.info('PtzCam object deletion.')

    def get_exposure(self):
        vst = {'VideoSourceToken': self.video_source.token}
        self.imaging_settings = self.imaging_service.GetImagingSettings(vst)

        exp_time = self.imaging_settings.Exposure.ExposureTime
        gain = self.imaging_settings.Exposure.Gain
        iris = self.imaging_settings.Exposure.Iris

        return exp_time, gain, iris

    def _send_imaging_settings(self):
        command_dict = {'VideoSourceToken': self.video_source.token,
                        'ImagingSettings': self.imaging_settings}
        self.imaging_service.SetImagingSettings(command_dict)

    def set_exposure_to_auto(self):
        self.imaging_settings.Exposure['Mode'] = 'AUTO'
        self._send_imaging_settings()

    def set_focus_to_auto(self):
        self.imaging_settings.Focus['AutoFocusMode'] = 'AUTO'
        self._send_imaging_settings()

    def set_focus_to_manual(self):
        self.imaging_settings.Focus['AutoFocusMode'] = 'MANUAL'
        self._send_imaging_settings()

    def set_exposure_time(self, exposure_time):
        # need to implement bound checking using bounds gotten in constructor
        self.imaging_settings.Exposure['Mode'] = 'MANUAL'
        self.imaging_settings.Exposure['ExposureTime'] = exposure_time
        self._send_imaging_settings()

    def set_iris(self, iris):
        # need to implement bound checking using bounds gotten in constructor
        self.imaging_settings.Exposure['Mode'] = 'MANUAL'
        self.imaging_settings.Exposure['Iris'] = iris
        self._send_imaging_settings()

    def set_gain(self, gain):
        # need to implement bound checking using bounds
        self.imaging_settings.Exposure['Mode'] = 'MANUAL'
        self.imaging_settings.Exposure['Gain'] = gain
        self._send_imaging_settings()

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
        x_velocity = float(_check_zeroness(x_velocity))
        y_velocity = float(_check_zeroness(y_velocity))
        zoom_command = _check_zeroness(zoom_command)

        move_request = self.ptz_service.create_type('ContinuousMove')
        move_request.ProfileToken = self.media_profile.token
        move_request.Velocity = {'PanTilt': {'x': x_velocity, 'y': y_velocity},
                                 'Zoom': {'x': zoom_command}}
        self.ptz_service.ContinuousMove(move_request)

    def _prep_abs_move(self):
        """Prep move request

        """
        mov_req = self.ptz_service.create_type('AbsoluteMove')
        mov_req.ProfileToken = self.media_profile.token
        if mov_req.Position is None:
            t_dict = {'ProfileToken': self.media_profile.token}
            mov_req.Position = self.ptz_service.GetStatus(t_dict).Position
            mov_req.Speed = self.media_profile.PTZConfiguration.DefaultPTZSpeed

        return mov_req

    def get_position(self):
        move_request = self.ptz_service.create_type('AbsoluteMove')
        move_request.ProfileToken = self.media_profile.token
        token_dict = {'ProfileToken': self.media_profile.token}
        position = self.ptz_service.GetStatus(token_dict).Position

        # x = pan, y = tilt
        return (position['PanTilt']['x'],
                position['PanTilt']['y'],
                position['Zoom']['x'])

    def absmove(self, x_pos, y_pos):
        move_request = self._prep_abs_move()
        move_request.Position.PanTilt.x = x_pos
        move_request.Position.PanTilt.y = y_pos
        self.ptz_service.AbsoluteMove(move_request)

    def twitch(self):
        pan, tilt, zoom = self.get_position()

        pan_2 = np.clip(pan + 0.1, *self.pan_bounds)
        tilt_2 = np.clip(tilt + 0.2, *self.tilt_bounds)

        self.absmove_w_zoom(pan, tilt_2, zoom)
        time.sleep(1.0)
        self.absmove_w_zoom(pan_2, tilt_2, zoom)
        time.sleep(1.0)
        self.absmove_w_zoom(pan_2, tilt, zoom)
        time.sleep(1.0)
        self.absmove_w_zoom(pan, tilt, zoom)
        time.sleep(1.0)

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
        zoom_pos = _check_zeroness(zoom_pos)
        pan_pos = _check_zeroness(pan_pos)
        tilt_pos = _check_zeroness(tilt_pos)

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
               or tilt <= tilt_goal - close_enough
               or zoom >= zoom_goal + close_enough
               or zoom <= zoom_goal - close_enough):
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
        zoom_command = _check_zeroness(zoom_command)

        move_request = self._prep_abs_move()
        move_request.Position.Zoom.x = zoom_command
        self.ptz_service.AbsoluteMove(move_request)

    def stop(self):
        move_request = self._prep_abs_move()
        self.ptz_service.Stop({'ProfileToken': move_request.ProfileToken})
