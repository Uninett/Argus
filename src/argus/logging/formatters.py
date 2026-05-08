from logging import Formatter

__all__ = [
    "EnvironmentFormatter",
    "JSONEnvironmentFormatter",
]


class EnvironmentMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from django import settings

        self.ENVIRONMENT = getattr(settings, "ENVIRONMENT", None)


class EnvironmentFormatter(EnvironmentMixin, Formatter):
    def format(self, record):
        if not hasattr(record, "environment"):
            record.environment = self.ENVIRONMENT
        super().format(record)


try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    JSONEnvironmentFormatter = EnvironmentFormatter

else:

    class JSONEnvironmentFormatter(EnvironmentMixin, JsonFormatter):
        def process_log_record(self, log_data):
            if not hasattr(log_data, "environment"):
                log_data.environment = self.ENVIRONMENT
