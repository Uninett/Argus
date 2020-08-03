from datetime import datetime

from django.db import models

import argus.site.datetime_utils as utils


class DateTimeInfinityField(models.DateTimeField):
    # Code based on https://github.com/Uninett/nav/blob/44a67a5037305c946eb69666d0a4b3b51ea5cff4/python/nav/models/fields.py#L41-L53
    def get_db_prep_value(self, value, connection, prepared=False):
        is_postgres = self.is_postgres(connection)

        if isinstance(value, datetime):
            infinity_repr = utils.infinity_repr(value, str_repr=is_postgres)
            if infinity_repr:
                # (Presumably) only PostgreSQL accepts - and correctly adapts - infinity strings
                if is_postgres:
                    return connection.ops.adapt_datetimefield_value(infinity_repr)
                return infinity_repr
        elif isinstance(value, str):
            infinity_time = utils.parse_infinity(value, return_localized=False)
            if infinity_time:
                return value if is_postgres else infinity_time

        return super().get_db_prep_value(value, connection, prepared=prepared)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value

        return utils.infinity_time(value) or utils.convert_datetimefield_value(value, connection)

    def to_python(self, value):
        return utils.infinity_time(value) or super().to_python(value)

    @staticmethod
    def is_postgres(connection):
        return connection.settings_dict["ENGINE"].startswith("django.db.backends.postgresql")
