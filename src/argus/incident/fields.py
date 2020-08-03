from datetime import datetime

from django.db import models

import argus.site.datetime_utils as utils


class DateTimeInfinityField(models.DateTimeField):
    # Code based on https://github.com/Uninett/nav/blob/44a67a5037305c946eb69666d0a4b3b51ea5cff4/python/nav/models/fields.py#L41-L53
    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, datetime):
            infinity_repr = utils.infinity_repr(value)
            if infinity_repr:
                # (Presumably) only PostgreSQL accepts - and correctly adapts - infinity strings
                if self.is_postgres(connection):
                    return connection.ops.adapt_datetimefield_value(infinity_repr)
                return infinity_repr
        elif utils.parse_infinity(value):
            return value

        return super().get_db_prep_value(value, connection, prepared=prepared)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value

        return utils.infinity_time(value) or utils.convert_datetimefield_value(value, connection)

    def to_python(self, value):
        return utils.infinity_time(value) or super().to_python(value)

    def db_type(self, connection):
        data = self.db_type_parameters(connection)

        if self.is_postgres(connection):
            internal_type = "DateTimeField"
        else:
            internal_type = "CharField"
            data["max_length"] = 32  # slightly longer than datetime's string representation

        return connection.data_types[internal_type] % data

    def get_internal_type(self):
        return models.Field.get_internal_type(self)

    @staticmethod
    def is_postgres(connection):
        return connection.settings_dict["ENGINE"].startswith("django.db.backends.postgresql")
