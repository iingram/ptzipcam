from datetime import datetime

from onvif import ONVIFCamera


def connectCam(ip='192.168.1.168',
               port=8999):
    """
    Parameters
    ----------
    ip : str
       IP of camera to connect to

    port: int
       ONVIF port of camera

    Returns
    -------
    ONVIFCamera object
    """
    # camera = ONVIFCamera('192.168.1.64',
    #                      80,
    #                      'username',
    #                      'password',
    #                      '/etc/onvif/wsdl/')

    camera = ONVIFCamera(ip,
                         port,
                         'username',
                         'password',
                         '/etc/onvif/wsdl/')

    return camera


def printHost(mycam):
    """
    Prints hostname of connected camera

    Parameters
    ----------
    mycam : ONVIFCamera
      ONVIFCamera object connected to a connected camera

    """
    resp = mycam.devicemgmt.GetHostname()
    print 'This camera`s hostname: ' + str(resp.Name)


def printTime(mycam):
    print('NOTE: this in UTC time.')

    dt = mycam.devicemgmt.GetSystemDateAndTime()
    # tz = dt.TimeZone
    # year = dt.UTCDateTime.Date.Year
    # day = dt.UTCDateTime.Date.Day
    # hour = dt.UTCDateTime.Time.Hour
    # second = dt.UTCDateTime.Time.Second

    print(dt.UTCDateTime)


def setToCurrentDateTime(mycam):
    now = datetime.utcnow()

    time_params = mycam.devicemgmt.create_type('SetSystemDateAndTime')

    time_params.DateTimeType = 'Manual'
    time_params.DaylightSavings = True
    time_params.TimeZone.TZ = 'UTC+7'
    time_params.UTCDateTime.Date.Year = now.year
    time_params.UTCDateTime.Date.Month = now.month
    time_params.UTCDateTime.Date.Day = now.day
    time_params.UTCDateTime.Time.Hour = now.hour
    time_params.UTCDateTime.Time.Minute = now.minute
    time_params.UTCDateTime.Time.Second = now.second

    mycam.devicemgmt.SetSystemDateAndTime(time_params)
