from datetime import datetime

from django.template.defaultfilters import date


def get_datetime_format_length(datetime_format):
    return len(date(datetime_format, datetime.max))
