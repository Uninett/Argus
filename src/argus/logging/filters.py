import logging


__all__ = [
    "EnvironmentFilter",
]


class EnvironmentFilter(logging.Filter):
    "Attach deployment-specific context to log records"

    def __init__(self, name=""):
        super().__init__(name)

        from django import settings

        self.ENVIRONMENT = getattr(settings, "ENVIRONMENT", None)

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Modify the LogRecord in place, then return True so the record is logged.
        """
        if not hasattr(record, "environment"):
            record.environment = self.ENVIRONMENT
        return True
