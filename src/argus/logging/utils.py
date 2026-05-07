import logging
import logging.config

from django.utils.module_loading import import_string


__all__ = [
    "setup_logging",
    #     "update_loglevels",
]


def setup_logging(dotted_path=None):
    """Use the dictionary on the dotted path to set up logging

    Returns the dictionary on success, otherwise None.
    """
    _add_logging_level("TRACE", 5)

    if dotted_path:
        try:
            class_or_attr = import_string(dotted_path)
        except AttributeError:
            return

        logging.config.dictConfig(class_or_attr)
        return class_or_attr


# Removed until needed. Should be changed to be idempotent, but that requires
# dumping the existing config as a dict first.
# def update_loglevels(loglevel: str = "INFO", loggers=(), handlers=()) -> None:
#     """Override specific loglevels in already setup loggers or handlers"""
#     loglevel = loglevel.upper()
#     for logger in loggers:
#         logging.getLogger(logger).setLevel(loglevel)
#     if handlers:
#         handlerdict = {}
#         for handler in handlers:
#             handlerdict[handler] = {"level": loglevel}
#         logdict = {
#             "version": 1,
#             "disable_existing_loggers": False,
#             "incremental": True,
#             "handlers": handlerdict,
#         }
#         logging.config.dictConfig(logdict)


def _add_logging_level(level_name, level_num):
    if hasattr(logging, level_name):
        return
    logging.addLevelName(level_num, level_name)

    def log_with_custom_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    setattr(logging.Logger, level_name.lower(), log_with_custom_level)


# Readthedocs fails the build without this
_add_logging_level("TRACE", 5)
