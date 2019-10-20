import datetime

from src.aas.site.alert.models import Notification_profile, Alert


def isBetween(profile: Notification_profile, alert: Alert):
    """

    :param profile: Notification_profile
    :param alert: alert instance
    :return: Boolean
    True if the alert is within the given profile's desired interval
    True if noe interval is set for the profile
    False if the alert is outside of the given profile's desired interval
    """
    if profile.interval_start == None:
        return True

    if alert.timestamp.time() > profile.interval_start.time() and alert.timestamp.time() < profile.interval_stop.time():
        return True
    else:
        return False


